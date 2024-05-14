import asyncio
import re
import time
import json
from bs4 import BeautifulSoup
import requests
# read config ini file
import configparser


config = configparser.ConfigParser()
config.read('webscraping.ini')

# set data in config file
year = config['config'].get('year')
semester = config['config'].get('semester')

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}


class KKU:
    dataALL = []

    def getSubjectsID(self, f_data: str = None, data: set = set()):
        f_data = {
            'coursestatus': 'O00',
            'facultyid': '051General',
            'maxrow': '1000',
            'Acadyear': year,
            'Semester': semester,
        } if not f_data else f_data

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
            cells = row.find_all('td')
            id = cells[1].find('a')['href'].split('courseid=')[1].split('&')[0]
            data.add(id)

        # get nextPages
        try:
            if soup.find_all('tr')[-1].select_one('td:nth-child(2) > a')['href']:
                # get page
                next_f_data = soup.find_all(
                    'tr')[-1].select_one('td:nth-child(2) > a')['href'].split('class_info_1.asp?')[1]
                return self.getSubjectsID(next_f_data)
        except Exception:
            pass

        return data

    def getDetails(self, id: str):
        params = {
            'courseid': id,
            'acadyear': year,
            'semester': semester,
        }

        response = requests.get(
            'https://reg-mirror.kku.ac.th/registrar/class_info_2.asp',
            params=params,
            headers=headers,
        )

        # bs4
        resp = BeautifulSoup(response.content, 'html.parser')

        # select table by CSS selector
        soup = resp.select('table')[3]

        # remove all class="HeaderDetail"
        for header in soup.find_all(class_="HeaderDetail"):
            header.extract()

        # Initial data
        data: list = []

        # get rows
        rows = soup.find_all('tr')
        for index in range(4, len(rows)):
            row = rows[index]
            # if not row is class "NormalDetail" or align="left"
            if len(row.find_all('td')) < 10:
                continue
            cells = row.find_all('td')
            sec = int(str(cells[1].text.strip()))
            day = cells[3].text.strip()
            time = cells[4].text.strip()
            room = cells[5].text.strip()
            recive = int(cells[8].text.strip())
            remain = int(cells[10].text.strip())

            # format day
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

            # get data form font
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
                'recive': recive,
                'remain': remain,
                'mid': mid,
                'fin': fin,
                'lecturer': lecturer,
            }

            # append more attribute to data to dataALL refer id and sec
            self.dataALL.append(course)

    def run(self):
        subjects = self.getSubjectsID()
        for subject in subjects:
            self.getDetails(subject)

        # write to json file
        with open('Group/KKU/dataALL.json', 'w', encoding='utf-8') as f:
            json.dump(self.dataALL, f, ensure_ascii=False, indent=4)

class MSU:
    dataALL = []

    def scrap(self, f_data: str = None, coursecode:str = "004*"):
        if not f_data:
            f_data = {
                'facultyid': 'all',
                'maxrow': '1000',
                'Acadyear': year,
                'semester': semester,
                'coursecode': coursecode,
            }
     

        response = requests.post('https://reg.msu.ac.th/registrar/class_info_1.asp', headers=headers, data=f_data)

        # check status
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        # BeautifulSoup
        resp = BeautifulSoup(response.content, 'html.parser')

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
                print()
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
                print()

            try:
                split_data = time.split("สอบปลายภาค")
                final = split_data[1].strip()
            except:
                print()


            try:
                split_data = time.split("สอบกลางภาค")
                time = split_data[0].strip()
            finally:
                try:
                    split_data = time.split("สอบปลายภาค")
                    time = split_data[0].strip()
                except:
                    print()

            # Define the regular expression pattern
            pattern = r'(\d+)([A-Za-z])'
            # Find all matches in the string
            matches = re.findall(pattern, time)
            # Insert "&" between the number and alphabet character
            time = re.sub(pattern, r'\1 & \2', time)


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

        # get nextPages
        try:
            if soup.find_all('tr', class_='normalDetail')[-1].select_one('td:nth-child(2) > a')['href']:
                # get page
                next_f_data = soup.find_all('tr', class_='normalDetail')[-1].select_one('td:nth-child(2) > a')['href'].split('class_info_1.asp?')[1]
                print(next_f_data)
                return self.scrap(next_f_data)
        except Exception:
            print("End")
            pass

    def splitData(self, type:str = "GE"):
        # Create a dictionary for each course and append it to the data list
        GE1 = []
        GE2 = []
        GE3 = []
        GE4 = []
        GE5 = []
        
        for course in self.dataALL:
            if course['type'] == 'GE-1':
                GE1.append(course)
            elif course['type'] == 'GE-2':
                GE2.append(course)
            elif course['type'] == 'GE-3':
                GE3.append(course)
            elif course['type'] == 'GE-4':
                GE4.append(course)
            elif course['type'] == 'GE-5':
                GE5.append(course)
            
        # Save the JSON data to the file
        for i in range(1,6):
            with open(f"Group/MSU/GE-{i}.json", "w", encoding="utf-8") as file:
                json.dump(eval(f"GE{i}"), file, indent=4, ensure_ascii=False)

    def run(self):
        self.scrap()

        # sort list by remain most
        self.dataALL.sort(key=lambda x: x['remain'], reverse=True)

        # Save the JSON data to the file
        with open(f"Group/MSU/dataALL.json", "w", encoding="utf-8") as file:
            json.dump(self.dataALL, file, indent=4, ensure_ascii=False)

        self.splitData()

class UBU:
    dataALL = []

    def scrap(self, f_data: str = None, coursecode:str = "004*"):
        if not f_data:
            f_data = {
                'facultyid': 'all',
                'maxrow': '1000',
                'Acadyear': year,
                'semester': semester,
                'coursecode': coursecode,
            }
     

        response = requests.post('https://reg.msu.ac.th/registrar/class_info_1.asp', headers=headers, data=f_data)

        # check status
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return

        # BeautifulSoup
        resp = BeautifulSoup(response.content, 'html.parser')

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
                print()
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
                print()

            try:
                split_data = time.split("สอบปลายภาค")
                final = split_data[1].strip()
            except:
                print()


            try:
                split_data = time.split("สอบกลางภาค")
                time = split_data[0].strip()
            finally:
                try:
                    split_data = time.split("สอบปลายภาค")
                    time = split_data[0].strip()
                except:
                    print()

            # Define the regular expression pattern
            pattern = r'(\d+)([A-Za-z])'
            # Find all matches in the string
            matches = re.findall(pattern, time)
            # Insert "&" between the number and alphabet character
            time = re.sub(pattern, r'\1 & \2', time)


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

        # get nextPages
        try:
            if soup.find_all('tr', class_='normalDetail')[-1].select_one('td:nth-child(2) > a')['href']:
                # get page
                next_f_data = soup.find_all('tr', class_='normalDetail')[-1].select_one('td:nth-child(2) > a')['href'].split('class_info_1.asp?')[1]
                print(next_f_data)
                return self.scrap(next_f_data)
        except Exception:
            print("End")
            pass

    def splitData(self, type:str = "GE"):
        # Create a dictionary for each course and append it to the data list
        GE1 = []
        GE2 = []
        GE3 = []
        GE4 = []
        GE5 = []
        
        for course in self.dataALL:
            if course['type'] == 'GE-1':
                GE1.append(course)
            elif course['type'] == 'GE-2':
                GE2.append(course)
            elif course['type'] == 'GE-3':
                GE3.append(course)
            elif course['type'] == 'GE-4':
                GE4.append(course)
            elif course['type'] == 'GE-5':
                GE5.append(course)
            
        # Save the JSON data to the file
        for i in range(1,6):
            with open(f"Group/MSU/GE-{i}.json", "w", encoding="utf-8") as file:
                json.dump(eval(f"GE{i}"), file, indent=4, ensure_ascii=False)

    def run(self):
        self.scrap()

        # sort list by remain most
        self.dataALL.sort(key=lambda x: x['remain'], reverse=True)

        # Save the JSON data to the file
        with open(f"Group/MSU/dataALL.json", "w", encoding="utf-8") as file:
            json.dump(self.dataALL, file, indent=4, ensure_ascii=False)

        self.splitData()


# MSU().run()
UBU().run()
# KKU().run()