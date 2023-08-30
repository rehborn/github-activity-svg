"""

generate activity svg
"""
import argparse
import os
from calendar import Calendar
from datetime import datetime
from string import Template

import drawsvg as draw
import drawsvg.types
import requests
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'
GITHUB_GRAPHQL_CONTRIBUTIONS = """
query { 
  user(login: "$username"){
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""

# themes
THEME_GITHUB = {
    'default_color': '#bbddbb',
    'color1': '#55aa55',
    'color2': '#009933',
    'color3': '#006600',
    'color4': '#004d00',
    'color1_threshold': 1,
    'color2_threshold': 10,
    'color3_threshold': 20,
    'color4_threshold': 30,
}
THEME_WAKATIME = {
    'default_color': '#b3d9ff',
    'color1': '#6699ff',
    'color2': '#3366ff',
    'color3': '#0039e6',
    'color1_threshold': 1,
    'color2_threshold': 8,
    'color3_threshold': 12,
}

THEME_RETRO = {
    # 'default_color': '#660066',
    'label_color': 'black',
    'color1': 'cyan',
    'color2': 'magenta',
    'color3': 'red',
    'color1_threshold': 1,
    'color2_threshold': 20,
    'color3_threshold': 30,
}


def render_calendar(year: int, month: int, data: {}, theme: {}) -> drawsvg.Drawing:
    """
    Render Monthly Activity Calendar as SVG

    :param year: 1970
    :param month: 1-12
    :param data: {"datetime": "amount"}
    :param theme: {}
    :return: SVG
    """

    size = theme.get("size", 40)
    cal = Calendar(firstweekday=0)
    _svg = draw.Drawing(theme.get("width", 296), theme.get("height", 212), origin='top-left')

    # background
    if theme.get('background', None):
        _svg.append(draw.Rectangle(0, 0,
                                   theme.get("width", 296),
                                   theme.get("height", 212),
                                   fill=theme.get('background')))

    for week_num, week in enumerate(cal.monthdayscalendar(year, month)):
        for day_num, day in enumerate(week):
            if day == 0:
                continue

            _val = data.get(datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d'))
            fill = theme.get("default_color", '#ebedf0')

            if _val and day:
                if _val >= theme.get("color1_threshold", 1):
                    fill = theme.get("color1", '#99cc99')
                if _val >= theme.get("color2_threshold", 5):
                    fill = theme.get("color2", '#99cc99')
                if _val >= theme.get("color3_threshold", 10):
                    fill = theme.get("color3", '#99cc99')
                if _val >= theme.get("color3_threshold", 10):
                    fill = theme.get("color3", '#99cc99')
                if _val >= theme.get("color4_threshold", 99999):
                    fill = theme.get("color4")

            pos_x = (day_num * size) + (day_num * 2)
            pos_y = (week_num * size) + (week_num * 2)

            _svg.append(draw.Rectangle(pos_x + 2, pos_y + 2,
                                       size, size,
                                       fill=fill,
                                       rx='3', ry='3',
                                       fill_opacity=1))
            if day != 0:
                label = draw.Text(str(day), 16,
                                  pos_x + size / 2 + 2,
                                  pos_y + size / 2 + 2,
                                  fill=theme.get("label_color", "#ffffff"),
                                  center=True,
                                  font_family='Monospace',
                                  font_weight='bold')
                _svg.append(label)
    return _svg


def fetch_wakatime_data(url: str) -> {}:
    """fetch Wakatime JSON and create calendar svg"""
    response = requests.get(url, timeout=10)
    wakatime_json = response.json()

    data = {}
    for item in wakatime_json.get('data'):
        _date = datetime.strptime(item['range']['date'], '%Y-%m-%d')
        _hours = int(item['grand_total']['hours'])
        data[_date] = _hours

    return data


def fetch_github_data(username, token: str) -> {}:
    """fetch GitHub contributions and create calendar svg"""

    def query_github(__query):
        _headers = {"Authorization": f"Bearer {token}"}
        _json = {'query': __query}
        _request = requests.post(GITHUB_GRAPHQL_URL, json=_json, headers=_headers, timeout=10)
        return _request.json()

    # query contributions
    query_template = Template(GITHUB_GRAPHQL_CONTRIBUTIONS)
    query = query_template.substitute(username=username)
    response = query_github(query)
    data = {}
    _data = response.get('data')['user']['contributionsCollection']['contributionCalendar']['weeks']
    for weeks in _data:
        for contribution_days in weeks['contributionDays']:
            _date = datetime.strptime(contribution_days['date'], '%Y-%m-%d')
            data[_date] = contribution_days['contributionCount']

    return data


if __name__ == '__main__':
    load_dotenv()

    parser = argparse.ArgumentParser(description='Simple Resume and VCard Generator')
    parser.add_argument('--months', '-m', type=int, default=3, help='number of months to generate')
    parser.add_argument("--work-dir", type=str, default=".", help="working directory")
    parser.add_argument("--dist-dir", type=str, default="dist/", help="output directory")

    args = parser.parse_args()

    dist_path = os.path.join(args.work_dir, args.dist_dir)
    if not os.path.isdir(dist_path):
        print(f"trying to create {dist_path}")
        os.mkdir(dist_path)

    today = datetime.now()
    wakatime_json_url = os.getenv('WAKATIME_JSON_URL', None)
    gh_token = os.getenv('GH_TOKEN', None)
    gh_actor = os.getenv('GH_ACTOR', None)

    if gh_token and gh_actor:
        print("GH_TOKEN and GH_ACTOR found: generating github activity")
        github_data = fetch_github_data(gh_actor, gh_token)
        for i in range(0, args.months):
            date = today - relativedelta(months=i)
            svg = render_calendar(date.year, date.month, github_data, THEME_GITHUB)
            svg.save_svg(os.path.join(dist_path, f'github-{i}.svg'))

    if wakatime_json_url:
        print("WAKATIME_JSON_URL found: generating github activity")
        wakatime_data = fetch_wakatime_data(wakatime_json_url)
        for i in range(0, args.months):
            date = today - relativedelta(months=i)
            svg = render_calendar(date.year, date.month, wakatime_data, THEME_WAKATIME)
            svg.save_svg(os.path.join(dist_path, f'wakatime-{i}.svg'))
