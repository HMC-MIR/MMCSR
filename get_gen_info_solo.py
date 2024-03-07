import pickle
import requests
import re
from bs4 import BeautifulSoup
from tqdm import tqdm

# find general information section

def get_gen_info_solo(url_list, instrument='Piano'):
    '''
    same as get_gen_info but for solo piano pieces that don't have pdf ids
    
    
    '''
    attribute_list = ['Work Title', 'Alt\nernative\n.\nTitle', 'Name Translations', 'Name Aliases', 'Authorities', 'Composer',
                            'Opus/Catalogue Number', 'I-Catalogue Number', 'Key', 'Movements/Sections', 'Fisrt Performance', 'Year/Date of Composition', 
                            'First Pub\nlication', 'Librettist', 'Language', 'Copyright Information','Dedication', 'Average Duration', 'Composer Time Period', "Piece Style"]
    list_of_deletable_headings = ['Opus/Catalogue Number','I-Catalogue Number','Movements/Sections','Year/Date of Composition','First Pub\nlication','Average Duration','Composer Time Period']
    bad_heading_pattern = r'^.*\n'

    composer_dict = {}
    
    with tqdm(total=len(url_list), unit='iter', unit_scale=True, desc='Progress', ncols=100) as pbar:
        for url in url_list:
            parsed_text = retrieve_general_information(url)

            if parsed_text:

                info_dic = {}

                present_attributes = []
                # check which attributes are present in the parsed text
                for attribute in attribute_list:
                    if parsed_text.find(attribute) != -1:
                        present_attributes.append(attribute)

                # extract the text for each present attribute
                for attribute in attribute_list[:-1]:
                    if attribute in present_attributes:
                        info_dic[attribute] = extract_text_between_strings_new(parsed_text, attribute, present_attributes[present_attributes.index(attribute) + 1] if present_attributes.index(attribute) != len(present_attributes) - 1 else "Romantic")

                info_dic['Piece Style'] = parsed_text[parsed_text.find('Piece Style')+12:] # extract the piece style from the end of the general information section
                info_dic['Instrumentation'] = instrument
                info_dic['url'] = url

                if 'Alt\nernative\n.\nTitle' in present_attributes:
                    alt_title = info_dic['Alt\nernative\n.\nTitle']
                    info_dic['Alternative Title'] = alt_title
                    del info_dic['Alt\nernative\n.\nTitle']

                if 'First Pub\nlication' in present_attributes:
                    alt_title = info_dic['First Pub\nlication']
                    info_dic['First Publication'] = alt_title
                    del info_dic['First Pub\nlication']

                for heading in list_of_deletable_headings:
                    if heading in info_dic.keys():
                        try:
                            info_dic[heading] = re.sub(bad_heading_pattern, '', info_dic[heading])
                        except:
                            pass

                if info_dic['Composer'] in composer_dict.keys():
                    composer_dict[info_dic['Composer']][info_dic['Work Title']] = info_dic
                else:
                    composer_dict[info_dic['Composer']] = {info_dic['Work Title']:info_dic}
                

            else:
                print(f"Failed to retrieve information for {url}.")
                
            pbar.update(1)
            
    return composer_dict

# functions to get page text and parse out the general information sectioin

def get_page_text(url):
    '''Retrive the text from url.'''
    # parse web content into English text
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for any request errors

        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract all text from the page, excluding script and style tags
        text = soup.get_text(separator='\n', strip=True)

        return text
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def extract_text_between_strings_second(text, start_string, end_string):
    '''
    Extracts the substring between the second occurrence of start_string and end_string in text.
    '''
    # Find the second occurrence of the start_string (the second occurence of "general information" gives us our metadata)
    if text:
        start_index = text.find(start_string, text.find(start_string) + len(start_string))
        if start_index == -1:  # If start_string is not found
            return None

        # Find the occurrence of the end_string
        end_index = text.find(end_string, start_index)
        if end_index == -1:  # If end_string is not found
            return None

        # Extract the substring between the second occurrence of start_string and end_string
        extracted_text = text[start_index + len(start_string):end_index].strip()

        return extracted_text

def retrieve_general_information(url):
    '''Retrieves the general information section from the IMSLP page of a musical score until Instrumentation.'''
    # retrieve the general information section
    parsed_text = extract_text_between_strings_second(get_page_text(url),'General Information','Instrumentation')
    return parsed_text

def extract_text_between_strings_new(text, start_string, end_string):
    '''
    Extracts the substring between start_string and end_string in text.
    '''
    start_index = text.find(start_string)
    if start_index == -1:  # If start_string is not found
        return None

    # Find the occurrence of the end_string
    end_index = text.find(end_string, start_index)
    if end_index == -1:  # If end_string is not found
        return None

    # Extract the substring between the second occurrence of start_string and end_string
    extracted_text = text[start_index + len(start_string):end_index].strip()

    return extracted_text

with open('/home/ctang/ttmp/MMCSR/solo_piano_urls.txt', 'r') as f:
    solo_piano_list = f.read().splitlines()

solo_piano_dict = get_gen_info_solo(solo_piano_list, instrument='Piano')

with open('solo_piano_metadata.pkl', 'wb') as f:
    pickle.dump(solo_piano_dict, f)