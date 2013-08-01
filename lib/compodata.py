import requests


def pms_path_generator(pms_root, party):
    cleaned_root = "%s/api/party/%s" % (pms_root.rstrip("/"), party)

    def pms_url(path):
        return "%s/%s" % (cleaned_root, path.lstrip())
    return pms_url


def download_compo_data(pms_url, username, password, party, compo_id):
    entries_url = pms_url("compo/%s/entries/" % compo_id)
    result = requests.get(entries_url, auth=(username, password), verify=False)
    entries = result.json()
    return entries


def parse_compo_entries(entries, force_display_author_name=False):

    output_data = []
    for entry in entries:
        entry_id = entry['id']
        title = entry['name']
        author = entry['credits']
        preview = entry['preview_link']
        author_name_visible = entry['compo']['show_credits']
        if force_display_author_name is True:
            author_name_visible = True
        compo_id = entry['compo']['slug']
        party_id = entry['compo']['party']['slug']

        full_pms_id = "%s/%s/%d" % (party_id, compo_id, entry_id)

        entry_output_data = {
            'id': full_pms_id,
            'title': title.strip(),
            'preview': preview,
            }
        if author_name_visible is True:
            entry_output_data['author'] = author.strip()
        else:
            entry_output_data['author'] = u"(author hidden until results)"

        comments = entry.get('comments', None) or None
        if comments is not None:
            comments = comments.replace("\r", "").strip()
            comments = comments.replace("\n", "</p><p>")
            entry_output_data['comments'] = comments.strip()

        output_data.append(entry_output_data)

    return output_data


def update_entry_preview(
    pms_root, username, password, full_pms_id, preview_link):

    party, compo_id, entry_id = full_pms_id.split("/")
    pms_url = pms_path_generator(pms_root, party)
    entry_url = pms_url("compo/%s/entry/%s/" % (compo_id, entry_id))

    request_data = 'preview_link=%s' % preview_link.encode("utf-8")
    print "%s/%s" % (full_pms_id, request_data)

    request_data = {'preview_link', preview_link.encode("utf-8")}
    headers = {'Content-Type': 'text/plain'}
    requests.put(entry_url, data=request_data, headers=headers, verify=False)


def get_categories(pms_url, username, password):
    categories_url = pms_url("compos/")
    result = requests.get(categories_url, auth=(username, password), verify=False)
    compos = result.json()
    for compo in compos:
        print compo['slug']

