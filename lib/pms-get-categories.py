import argparse
import compodata

parser = argparse.ArgumentParser()
parser.add_argument("pms_root")
parser.add_argument("pms_party")
parser.add_argument("pms_login")
parser.add_argument("pms_password")
args = parser.parse_args()

pms_url = compodata.pms_path_generator(args.pms_root, args.pms_party)

print compodata.get_categories(pms_url, args.pms_login, args.pms_password)
