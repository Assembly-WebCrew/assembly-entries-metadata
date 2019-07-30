import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument("upload_page")
parser.add_argument("upload_account")
parser.add_argument("upload_password")
parser.add_argument("import_file", type=argparse.FileType("rb"))
args = parser.parse_args()

result = requests.post(
    args.upload_page,
    data={"form.actions.import": "Import"},
    files={"form.data": args.import_file},
    auth=(args.upload_account, args.upload_password))

print(result.status_code)
