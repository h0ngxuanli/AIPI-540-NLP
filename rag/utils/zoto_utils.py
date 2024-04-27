from datetime import datetime
from pathlib import Path
from multiprocess import Pool
from pyzotero import zotero

def get_all_values(d):
    values = []
    for value in d.values():
        if isinstance(value, dict):
            # If the value is another dictionary, extend recursively
            values.extend(get_all_values(value))
        else:
            # Otherwise, add the value directly to the list
            values.append(value)
    return values

def get_meta_data(zot, key):
    sample = zot.item(key)
    items_info = dict(sample.items())["data"]

    collection_pairs = {}
    for item in zot.collections():
        collection_pairs[item["key"]] = item["data"]["name"]
    items_info = dict(sample.items())["data"]

    meta_data_info = {}
    for meta_data_key in ["dateAdded", "dateModified", "filename", "title", "creators", "abstract", "collections", "tags"]:

        if items_info.get(meta_data_key) is not None:

            if type(items_info.get(meta_data_key)) == type([]):

                if meta_data_key == "collections":
                    meta_data_info[meta_data_key] = collection_pairs[items_info[meta_data_key][0]]
                elif meta_data_key == "creators":
                    authors = []
                    for author in items_info["creators"]:
                        authors.append(author["firstName"] + " " + author["lastName"])
                    meta_data_info[meta_data_key] = authors
                elif meta_data_key == "tags":
                    tags = []
                    for tag in items_info["tags"]:
                        tags.append(tag['tag'])
                    meta_data_info[meta_data_key] = tags
            else:
                meta_data_info[meta_data_key] = items_info[meta_data_key]

        else:
            if meta_data_key in ["creators", "tags"]:
                meta_data_info[meta_data_key] = []
            else:
                meta_data_info[meta_data_key] = ""
    return meta_data_info

def get_paper_keys(zot, latest_time = None):
    keys = []
    added_time = []
    items = zot.items()
    
    for item in items:
        try:
            if 'application/pdf' in get_all_values(item):

                if latest_time is not None:
                    if datetime.strptime(item["data"]["dateAdded"], '%Y-%m-%dT%H:%M:%SZ') > datetime.strptime(latest_time, '%Y-%m-%dT%H:%M:%SZ'):
                        keys.append(item["key"])
                        added_time.append(item["data"]["dateAdded"])
                else:
                    keys.append(item["key"])
                    added_time.append(item["data"]["dateAdded"])

        except:
            continue
    
    # dates = [datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ') for date in added_time]
    # dates.sort()
    # sorted_date_strings = [date.strftime('%Y-%m-%dT%H:%M:%SZ') for date in dates]
    # latest_time = sorted_date_strings[-1]

    # Zip the lists together and sort by added_time
    zipped_lists = zip(added_time, keys)
    sorted_pairs = sorted(zipped_lists, reverse = True)
    # Unzip the lists back
    sorted_added_time, sorted_keys = zip(*sorted_pairs)

    # Convert tuples back to lists (if necessary)
    sorted_added_time = list(sorted_added_time)
    sorted_keys = list(sorted_keys)
    return sorted_keys, sorted_added_time

def pull_paper(zot, key, file_path):
    try:
        Path(file_path).mkdir(parents=True, exist_ok=True)
        zot.dump(key, f'article_{key}.pdf', file_path)
    except:
        pass

def pull_paper_wrapper(args):
    zot, key, file_path = args
    pull_paper(zot, key, file_path)

def pull_paper_parallelized(zot, file_path, num_processes, latest_time = None):
    paper_keys, sorted_time = get_paper_keys(zot, latest_time)

    with Pool(num_processes) as pool:
        args = [(zot, key, file_path) for key in paper_keys]
        pool.map(pull_paper_wrapper, args)

    latest_time = sorted_time[0]
    return latest_time


def initialize_zotero(library_id, api_key, library_type = "user"):
    zot = zotero.Zotero(library_id, library_type, api_key)
    return zot


