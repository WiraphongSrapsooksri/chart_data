# Import modules
import os
import re
import json
from bs4 import BeautifulSoup
import requests
import configparser
import multiprocessing

# Load config
config = configparser.ConfigParser()
config.read('webscraping.ini')

# Get config
year = config['config'].get('year')
semester = config['config'].get('semester')

# Set headers
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

# paths
folder = "Group"
paths = {
    "MSU",
    "KKU",
}

# check path if not create
for path in paths:
    path = os.path.join(folder, path)
    if not os.path.exists(path):
        os.makedirs(path)


import threading

class KKU:
    # Initial
    def __init__(self):
        # init data
        self.dataALL = []
        self.lock = threading.Lock()

    # Get all subjects
    def getSubjectsID(self, f_data: str = None, data: set = set()):
        # set default f_data
        f_data = {
            'coursestatus': 'O00',
            'facultyid': '051General',
            'maxrow': '1000',
            'Acadyear': year,
            'Semester': semester,
        } if not f_data else f_data

        # request web page with post method
        response = requests.post(
            'https://reg-mirror.kku.ac.th/registrar/class_info_1.asp',
            headers=headers,
            data=f_data,
        )

        # bs4
        resp = BeautifulSoup(response.content, 'html.parser')

        # select table by CSS selector
        soup = resp.select('table')[1]

        # Find all rows in the table, excluding the header and footer rows
        rows = soup.find_all('tr', class_='NormalDetail')
        for row in rows:
            # get cells
            cells = row.find_all('td')
            # get id
            id = cells[1].find('a')['href'].split('courseid=')[1].split('&')[0]
            # add id to data
            data.add(id)

        # get nextPages
        try:
            # if next page is not None
            if soup.find_all('tr')[-1].select_one('td:nth-child(2) > a')['href']:
                # get next page
                next_f_data = soup.find_all('tr')[-1].select_one('td:nth-child(2) > a')['href'].split('class_info_1.asp?')[1]
                return self.getSubjectsID(next_f_data)
        except Exception:
            pass

        return data

    # Get details
    def getDetails(self, id: str):
        # set params
        params = {
            'courseid': id,
            'acadyear': year,
            'semester': semester,
        }

        # request web page with get method
        response = requests.get(
            'https://reg-mirror.kku.ac.th/registrar/class_info_2.asp',
            params=params,
            headers=headers,
        )

        # bs4
        resp = BeautifulSoup(response.content, 'html.parser')

        # select table by CSS selector
        soup = resp.select('table')[3]

        # remove header in table
        for header in soup.find_all(class_="HeaderDetail"):
            header.extract()

        # get rows
        rows = soup.find_all('tr')
        for index in range(4, len(rows)):
            row = rows[index]
            # check if row is not subject
            if len(row.find_all('td')) < 10:
                continue

            # get cells, sec, get day, time, room, recive, remain
            cells = row.find_all('td')
            sec = int(str(cells[1].text.strip()))
            day = cells[3].text.strip()
            time = cells[4].text.strip()
            room = cells[5].text.strip()
            recive = int(cells[8].text.strip())
            remain = int(cells[10].text.strip())

            # set format day
            day = "Mo" if day == "จันทร์" else "Tu" if day == "อังคาร" else "We" if day == "พุธ" else "Th" if day == "พฤหัสบดี" else "Fr"

            # get info
            info_htmls = [
                rows[index+1].find_all('td'), rows[index+3].find_all('td')]

            lecturer, fin = [info[4].text.strip().replace(
                "  ", "") or None for info in info_htmls]

            # init sumrong
            sumrong = ""

            if rows[index+2].find_all('td')[4].find_all('br'):
                for br in rows[index+2].find_all('td')[4].find_all('br'):
                    sumrong += br.next_sibling.strip() + " / "
                sumrong = sumrong.replace("  ", "").replace("   ", " ")[:-3]
            else:
                sumrong = rows[index+2].find_all(
                    'td')[4].text.strip().replace("  ", "").replace("   ", " ")

            mid = None

            # get code, name, credit, type
            code = resp.select('font.NormalDetail')[0].text.strip()
            name = resp.select('font.NormalDetail')[1].text.strip()
            credit = resp.select('font.NormalDetail')[6].text.strip()
            type = "GE-"+code[2:3]

            # set course
            course = {
                'type': type,
                'code': code,
                'name': name,
                'note': sumrong,
                'credit': credit,
                'time': f'{day}{time} {room}',
                'sec': sec,
                'remain': remain,
                'recive': recive,
                'mid': mid,
                'fin': fin,
                'lecturer': lecturer,
            }

            # append more attribute to data to dataALL refer id and sec
            with self.lock:
                self.dataALL.append(course)

    def splitData(self):
        # Create a dictionary for each course and append it to the data list
        GE = {}

        for course in self.dataALL:
            if course['type'] not in GE:
                GE[course['type']] = []
            GE[course['type']].append(course)

        # Save the JSON data to the file
        for key in GE:
            with open(f"Group/KKU/{key}.json", "w", encoding="utf-8") as file:
                json.dump(GE[key], file, indent=4, ensure_ascii=False)

    # run
    def run(self):
        # get subjects
        subjects = self.getSubjectsID()
        threads = []
        # get details
        for subject in subjects:
            t = threading.Thread(target=self.getDetails, args=(subject,))
            threads.append(t)
            t.start()

        # wait for all threads to finish
        for t in threads:
            t.join()

        # sort data by remain most
        self.dataALL.sort(key=lambda x: x['remain'], reverse=True)

        # split data
        self.splitData()


        # save data to json file
        with open('Group/KKU/dataALL.json', 'w', encoding='utf-8') as f:
            json.dump(self.dataALL, f, ensure_ascii=False, indent=4)

class MSU:
    # init
    def __init__(self):
        # init data
        self.dataALL = []

    # scrap
    def scrap(self, f_data: str = None, coursecode:str = "004*"):
        # set post data
        if not f_data:
            f_data = {
                'facultyid': 'all',
                'maxrow': '1000',
                'Acadyear': year,
                'semester': semester,
                'coursecode': coursecode,
            }

        # request web page with post method
        response = requests.post('https://reg.msu.ac.th/registrar/class_info_1.asp', headers=headers, data=f_data)

        # check status
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        # convert from windows-874 charset to utf-8
        response.encoding = "windows-874"

        content_windows874 = response.content
        content_utf8 = content_windows874.decode("TIS-620").encode("utf-8")

        # BeautifulSoup
        resp = BeautifulSoup(content_utf8, 'html.parser')

        # select table by CSS selector
        soup = resp.select_one('body > div.contenttive > div:nth-child(1) > div.main > div > table:nth-child(6)')


        # Find all rows in the table, excluding the header and footer rows
        rows = soup.find_all('tr', class_='normalDetail')[1:-1]

        # Iterate over each row and extract the required information
        for row in rows:
            cells = row.find_all('td')
            code = cells[1].find('a').text.strip()
            subject_data = cells[2].decode_contents().split("<br/>")
            # TODO: มี font หลุดเข้ามาบางอัน
            name = subject_data[0].split("<font")[0]
            credit = cells[3].text.strip()
            time = cells[4].text.strip()
            sec = int(cells[5].text.strip())
            remain = int(cells[8].text.strip())
            receive = int(cells[6].text.strip())

            lecturer_raw = subject_data[0]
            try:
                lecturer_raw = subject_data[1]
            except:
                pass
            # Extract the <font> elements within the outer <font> element
            font_elements = re.findall(r'<font[^>]*>.*?</font>', lecturer_raw)
            # Extract the text content of the <li> elements
            li_text = [li for font in font_elements for li in re.findall(r'<li>.*?</li>', font)]
            # Remove the <li> tags from the extracted text
            li_text = [re.findall(r'<li>(.*?)<\/li>', nameLecture)[0].replace('<li>', ' / ') for nameLecture in li_text]
            # Join the extracted text with a delimiter
            lecturer = ' / '.join(li_text)

            # Find the first <font> element
            first_font = re.search(r'<font[^>]*>(.*?)</font>', lecturer_raw)

            # Remove any nested <font> elements within the first <font> element
            content = re.sub(r'<font[^>]*>.*?</font>', '', first_font.group(1))
            # Find the content before the <font> tag
            match = re.search(r'(.*?)<font', content)

            # Extract the content
            if match:
                content = match.group(1)
            else:
                content = ""

            mid = None
            final = None

            try:
                split_data = time.split("สอบปลายภาค")
                mid = split_data[0].strip().split("สอบกลางภาค")[1].strip()
            except:
                pass

            try:
                split_data = time.split("สอบปลายภาค")
                final = split_data[1].strip()
            except:
                pass


            try:
                split_data = time.split("สอบกลางภาค")
                time = split_data[0].strip()
            finally:
                try:
                    split_data = time.split("สอบปลายภาค")
                    time = split_data[0].strip()
                except:
                    pass

            # Define the regular expression pattern
            pattern = r'(\d+)([A-Za-z])'
            # Find all matches in the string
            matches = re.findall(pattern, time)
            # Insert "&" between the number and alphabet character
            time = re.sub(pattern, r'\1 & \2', time)

            # set type
            type = "GE-"+code[3:4]

            # Create a dictionary for each course and append it to the data list
            course = {
                'type': type,
                'code': code,
                'name': name,
                'note': content,
                'credit': credit,
                'time': time,
                'sec': sec,
                'remain':remain,
                'receive': receive,
                'mid': mid,
                'final': final,
                'lecturer': lecturer
            }
            self.dataALL.append(course)

        # check next page
        try:
            if soup.find_all('tr', class_='normalDetail')[-1].select_one('td:nth-child(2) > a')['href']:
                # set next page data
                next_f_data = soup.find_all('tr', class_='normalDetail')[-1].select_one('td:nth-child(2) > a')['href'].split('class_info_1.asp?')[1]
                print(next_f_data)
                return self.scrap(next_f_data)
        except Exception:
            pass

    # split data
    def splitData(self):
        # Create a dictionary for each course and append it to the data list
        GE = {}

        for course in self.dataALL:
            if course['type'] not in GE:
                GE[course['type']] = []
            GE[course['type']].append(course)

        # Save the JSON data to the file
        for key in GE:
            with open(f"Group/MSU/{key}.json", "w", encoding="utf-8") as file:
                json.dump(GE[key], file, indent=4, ensure_ascii=False)

    # run
    def run(self):
        # scrap data
        self.scrap()

        # sort list by remain most
        self.dataALL.sort(key=lambda x: x['remain'], reverse=True)

        # split data
        self.splitData()

        # Save the JSON data to the file
        with open(f"Group/MSU/dataALL.json", "w", encoding="utf-8") as file:
            json.dump(self.dataALL, file, indent=4, ensure_ascii=False)

class UBU:
    def __init__(self):
        self.dataALL = []
        self.manager = multiprocessing.Manager()
        self.result_list = self.manager.list()

    @staticmethod
    def scrap(result_list, f_data, coursecode):
        print(f_data)

        response = requests.post('https://reg2.ubu.ac.th/registrar/class_info_1.asp', headers=headers, data=f_data)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        resp = BeautifulSoup(response.content, 'html5lib')

        try:
            rows = resp.select('#page > table:nth-child(5) > tbody > tr > td:nth-child(3) > font > font > font > div > table > tbody > tr')[2:-1]

            for row in rows:
                cells = row.find_all('td')
                code = cells[1].find('a').text.strip()
                subject_data = cells[2].decode_contents().split("<br/>")
                name = subject_data[0].split("<font")[1].split(">")[1]
                credit = cells[3].text.strip().replace('(', ' (')
                raw_time = ' & '.join(cells[5].text.strip().replace('จ.', '|Mo').replace('อ.', '|Tu').replace('พ.', '|We').replace('พฤ.', '|Th').replace('ศ.', '|Fr').replace('ส.', '|Sa').replace('อา.', '|Su').split('|')[1:])
                time = raw_time.split('สอบ  ')[0]
                sec = int(cells[4].text.strip())
                remain = int(cells[7].text.strip())
                status = cells[8].text.strip()
                receive = int(cells[6].text.strip())

                if status == 'ปิด':
                    continue

                lecturer_raw = subject_data[0]
                try:
                    lecturer_raw = subject_data[1]
                except:
                    pass

                font_elements = re.findall(r'<font[^>]*>.*?</font>', lecturer_raw)
                li_text = [li for font in font_elements for li in re.findall(r'<li>.*?</li>', font)]
                li_text = [re.findall(r'<li>(.*?)<\/li>', nameLecture)[0].replace('<li>', ' / ') for nameLecture in li_text]
                lecturer = ' / '.join(li_text)

                first_font = re.search(r'<font[^>]*>(.*?)</font>', lecturer_raw)
                content = re.sub(r'<font[^>]*>.*?</font>', '', first_font.group(1)) if first_font else ""
                match = re.search(r'(.*?)<font', content)
                content = match.group(1) if match else ""

                mid = None
                final = None

                if len(raw_time.split('สอบ  ')) >= 2:
                    # Extract the regular class time
                    time_details = cells[5].text
                    # Extract mid and final exam times
                    mid_exam_matches = re.findall(r'M (\d{2}\/\d{2}\/\d{2} \d{2}:\d{2}-\d{2}:\d{2} [\w\d]+)', time_details)
                    final_exam_matches = re.findall(r'F (\d{2}\/\d{2}\/\d{2} \d{2}:\d{2}-\d{2}:\d{2} [\w\d]+)', time_details)
                    mid = ' & '.join(mid_exam_matches)
                    final = ' & '.join(final_exam_matches)
                #     try:
                #         split_data = raw_time.split('สอบ  ')[1].split("M ")
                #         mid = split_data[0].strip().split("M ")[1].strip()
                #     except:
                #         pass

                #     try:
                #         split_data = raw_time.split('สอบ  ')[1].split("F ")
                #         final = split_data[1].strip()
                #     except:
                #         pass

                pattern = r'(\d+)([A-Za-z])'
                time = re.sub(pattern, r'\1 & \2', time)

                type = "GE-" + code[0:4]

                course = {
                    'type': type,
                    'code': code,
                    'name': name,
                    'note': content,
                    'credit': credit,
                    'time': time,
                    'sec': sec,
                    'remain': remain,
                    'receive': receive,
                    'mid': mid,
                    'final': final,
                    'lecturer': lecturer
                }
                result_list.append(course)
        except Exception as e:
            print(f"Error processing: {e}")

    def splitData(self):
        GE = {}

        for course in self.dataALL:
            if course['type'] not in GE:
                GE[course['type']] = []
            GE[course['type']].append(course)

        for key in GE:
            with open(f"Group/UBU/{key}.json", "w", encoding="utf-8") as file:
                json.dump(GE[key], file, indent=4, ensure_ascii=False)

    def run(self):
        patterns = ["10*", "111*", "121*", "131*", "141*", "151*", "171*", "181*", "191*", "201*", "211*", "231*"]
        # patterns = ["141*"]

        tasks = []
        for pat in patterns:
            f_data = {
                'facultyid': 'all',
                'maxrow': '1000',
                'Acadyear': '2565',
                'semester': '1',
                'coursecode': pat,
                'page': 1
            }
            response = requests.post('https://reg2.ubu.ac.th/registrar/class_info_1.asp', headers=headers, data=f_data)
            if response.status_code == 200:
                resp = BeautifulSoup(response.content, 'html5lib')
                last_row = resp.select('#page > table:nth-child(5) > tbody > tr > td:nth-child(3) > font > font > font > div > table > tbody > tr')[-1]
                has_nextpage = len(last_row.find_all('a')) > 0
                if has_nextpage:
                    link_page = int(last_row.find_all('a')[-1].text.strip())
                    for page in range(1, link_page + 1):
                        f_data['page'] = page
                        tasks.append((self.result_list, f_data.copy(), pat))
                else:
                    tasks.append((self.result_list, f_data.copy(), pat))

        with multiprocessing.Pool() as pool:
            pool.starmap(UBU.scrap, tasks)

        self.dataALL.extend(self.result_list)

        self.dataALL.sort(key=lambda x: x['remain'], reverse=True)

        self.splitData()

        with open(f"Group/UBU/dataALL.json", "w", encoding="utf-8") as file:
            json.dump(self.dataALL, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    # time record
    # import time
    # start = time.time()
    # MSU().run()
    # KKU().run()
    UBU().run()
    # end = time.time()
    # print(f"Runtime of the program is {end - start}")
