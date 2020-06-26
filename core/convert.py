import base64
import json
import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import pdfkit


# Devtools handler
def send_devtools(driver, cmd, params={}):
    resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
    url = driver.command_executor._url + resource
    body = json.dumps({"cmd": cmd, "params": params})
    response = driver.command_executor._request("POST", url, body)

    if response.get("status"):
        raise Exception(response.get("value"))

    return response.get("value")


# Convert webpage to pdf
def web2pdf(url, path):
    webdriver_options = Options()
    webdriver_options.add_argument("--headless")
    webdriver_options.add_argument("--disable-gpu")
    browser = webdriver.Chrome(
        ChromeDriverManager().install(), options=webdriver_options
    )

    # load url
    browser.get(url)

    print_options = {
        "landscape": False,
        "displayHeaderFooter": False,
        "printBackground": True,
        "preferCSSPageSize": True,
    }

    result = send_devtools(browser, "Page.printToPDF", print_options)
    browser.quit()

    # save file
    with open(path, "wb") as f:
        f.write(base64.b64decode(result.get("data")))

    return path


# Convert html to pdf
def html2pdf(html, path):
    WKHTMLTOPDF_PATH = os.environ.get("WKHTMLTOPDF_PATH")

    # decide wkhtmltopdf path
    if WKHTMLTOPDF_PATH:
        configuration = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    else:
        configuration = pdfkit.configuration()

    pdfkit.from_string(html, path, configuration=configuration)
    return path


# convert parsed data to html
def data2pdf(data, path):
    # render template
    template = """
    <div style="text-align:center; margin-bottom: 5rem;">
        <h1 style="margin-bottom:1rem">{input_name} - CV</h1>
        <h5 style="color:#b7b7b7;margin-top:1rem">
            Parsed with <a href="https://artbiogs.com">https://artbiogs.com</a>
        </h5>
    </div>
    <table>
        <tbody>
            <tr>
                <td><b>Name</b></td>
                <td>{name}</td>
            </tr>
            <tr>
                <td><b>DOB</b></td>
                <td>{dob}</td>
            </tr>
            <tr>
                <td colspan="2" style="padding-bottom: 1rem;"><b>Solo Exhibitions:</b></td>
            </tr>
            {solo_exhibitions}
            <tr>
                <td colspan="2" style="padding-bottom: 1rem;padding-top: 1rem;"><b>Group Exhibitions:</b></td>
            </tr>
            {group_exhibitions}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2" style="padding-top: 4rem;">
                    Your reference id is: "{hash}". Contact <a href="mailto:support@art-prizes.com">support@art-prizes.com</a> for any enquiries.
                </td>
            </tr>
        </tfoot>    
    </table>

    <div style="text-align:center; margin-bottom: 5rem;page-break-before: always">
        <h1 style="margin-bottom:1rem">About your Scanned CV</h1>
        <h5 style="color:#b7b7b7;margin-top:1rem">
            Parsed with <a href="https://artbiogs.com">https://artbiogs.com</a>
        </h5>
    </div>
    <table style="width:100%">
        <tbody>
            <tr>
                <td><b>Submitted by Artist:</b></td>
                <td>{is_artist}</td>
            </tr>
            <tr>
                <td><b>Name:</b></td>
                <td>{input_name}</td>
            </tr>
            <tr>
                <td><b>Email:</b></td>
                <td>{input_email}</td>
            </tr>            
            <tr>
                <td><b>Parsed On:</b></td>
                <td>{parsedAt}</td>
            </tr>
            <tr>
                <td><b>Reference ID:</b></td>
                <td>{hash}</td>
            </tr>
            <tr>
                <td><b>IP Address:</b></td>
                <td>{ip}</td>
            </tr>
        </tbody>
    </table>
    """

    html_exhibitions = {"solo_exhibitions": "", "group_exhibitions": ""}

    # convert exhibitions to html bullets
    for t in ["solo_exhibitions", "group_exhibitions"]:
        for index, exhibition in enumerate(data.get(t, [])):
            # no title
            if not exhibition.get("title"):
                continue

            # bullet template
            li = "<tr><td colspan='2' style='padding-left: 3rem'>{year}: <u>{title}</u> {remaining}</td></tr>"

            # convert json to html
            html_exhibitions[t] += li.format(
                year=exhibition.get("year"),
                title=exhibition.get("title"),
                remaining=exhibition.get("original", "").replace(
                    exhibition.get("title"), ""
                ),
            )

    # populate template
    html = template.format(
        hash=data.get("meta", {}).get("hash") or "Not provided.",
        name=data.get("name") or "Not detected.",
        dob=data.get("dob") or "Not Detected.",
        solo_exhibitions=html_exhibitions.get("solo_exhibitions")
        or "<tr><td>Not detected.</td></tr>",
        group_exhibitions=html_exhibitions.get("group_exhibitions")
        or "<tr><td style='padding-left:2rem;'>Not detected.</td></tr>",
        input_name=data.get("meta", {}).get("input", {}).get("name") or "Not provided.",
        input_email=data.get("meta", {}).get("input", {}).get("email")
        or "Not provided.",
        is_artist="Yes"
        if data.get("meta", {}).get("input", {}).get("is_artist")
        else "No",
        parsedAt=data.get("meta", {}).get("parsedAt") or "Not Provided.",
        ip=data.get("meta", {}).get("ip") or "Not Provided.",
    )

    html2pdf(html, path)

    return path


if __name__ == "__main__":
    # web2pdf(sys.argv[1], sys.argv[2])

    data = {
        "name": "Annika Rameyn",
        "dob": "1986",
        "solo_exhibitions": [
            {
                "year": "2020",
                "title": "Endurance",
                "original": "Endurance, Flinders Lane Gallery, Melbourne.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2019",
                "title": "Endurance",
                "original": "Endurance, Megalo Print Studio and Gallery, Canberra.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2019",
                "title": "Upheaval",
                "original": "Upheaval, Goulburn Regional Art Gallery, Goulburn, NSW.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2018",
                "title": "Ghosts",
                "original": "Ghosts, Flinders Lane Gallery, Melbourne.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2018",
                "title": "Verge",
                "original": "Verge, Biennale of Australian Art, George Farmer Building,",
                "type": "solo_exhibitions",
            },
            {
                "year": "2018",
                "title": "Ballarat",
                "original": "Ballarat, Victoria.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2018",
                "title": "Composition in Blue",
                "original": "Composition in Blue, Belconnen Arts Centre, Canberra.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2017",
                "title": "Precipice",
                "original": "Precipice, ANCA Gallery, Canberra.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2015",
                "title": "Passage",
                "original": "Passage, Flinders Lane Gallery, Melbourne.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2013",
                "title": "Luminous Earth",
                "original": "Luminous Earth, Canberra Contemporary Art Space",
                "type": "solo_exhibitions",
            },
            {
                "year": "2013",
                "title": "Manuka",
                "original": "Manuka, Canberra.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2013",
                "title": "These Walls",
                "original": "These Walls, Port Jackson Press Print Room, Melbourne.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2012",
                "title": "Barranco",
                "original": "Barranco, Photospace Gallery, A.N.U. School of Art,",
                "type": "solo_exhibitions",
            },
            {
                "year": "2012",
                "title": None,
                "original": "Canberra.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2011",
                "title": "Drift",
                "original": "Drift, Belconnen Gallery, Belconnen Community Centre,",
                "type": "solo_exhibitions",
            },
            {
                "year": "2011",
                "title": None,
                "original": "Canberra.",
                "type": "solo_exhibitions",
            },
            {
                "year": "2011",
                "title": "Autumn Leaves",
                "original": "Autumn Leaves, Canberra Contemporary Art Space Manuka,",
                "type": "solo_exhibitions",
            },
            {
                "year": "2011",
                "title": None,
                "original": "Canberra.",
                "type": "solo_exhibitions",
            },
        ],
        "group_exhibitions": [],
        "meta": {
            "hash": "3727bc7c83af26d08cc00cd9f6e3ddd0",
            "input": {"name": "Annika Romeyn", "email": "annikaromeyn@gmail.com  "},
            "ip": "203.115.95.151",
            "createdAt": "2020-06-25 15:25:20",
            "parsedAt": "2020-06-25 15:26:37",
        },
    }

    data2pdf(data, "cv-parsed.pdf")
