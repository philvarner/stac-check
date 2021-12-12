from .validate import StacValidate
from .utilities import is_valid_url
import json
import os
from dataclasses import dataclass
import pystac
import requests
from urllib.parse import urlparse

@dataclass
class Linter:
    item: str
    assets: bool = False
    links: bool = False
    recursive: bool = False

    def __post_init__(self):
        self.data = self.load_data(self.item)
        self.message = self.validate_file(self.item)
        self.asset_type = self.check_asset_type()
        self.version = self.check_version()
        self.validator_version = "2.4.0"
        self.update_msg = self.set_update_message()
        self.valid_stac = self.message["valid_stac"]
        self.error_type = self.check_error_type()
        self.error_msg = self.check_error_message()
        self.invalid_asset_format = self.check_links_assets(10, "assets", "format") if self.assets else None
        self.invalid_asset_request = self.check_links_assets(10, "assets", "request") if self.assets else None
        self.invalid_link_format = self.check_links_assets(10, "links", "format") if self.links else None
        self.invalid_link_request = self.check_links_assets(10, "links", "request") if self.links else None
        self.schema = self.check_schema()
        self.summaries = self.check_summaries()
        self.num_links = self.get_num_links()
        self.recursive_error_msg = ""
        self.validate_all = self.recursive_validation(self.load_data(self.item))
        self.object_id = self.return_id()
        self.file_name = self.get_file_name()
        self.best_practices_msg = self.create_best_practices_msg()

    def load_data(self, file):
        if is_valid_url(file):
            resp = requests.get(file)
            data = resp.json()
        else:
            with open(file) as json_file:
                data = json.load(json_file)
        return data

    def validate_file(self, file):
        stac = StacValidate(file, links=self.links, assets=self.assets)
        stac.run()
        return stac.message[0]

    def recursive_validation(self, file):
        if self.recursive:
            try:
                catalog = pystac.read_dict(file)
                catalog.validate_all()
                return True
            except Exception as e:
                self.recursive_error_msg = f"Exception {str(e)}"
                return False

    def check_asset_type(self):
        if "asset_type" in self.message:
            return self.message["asset_type"]
        else:
            return ""

    def check_schema(self):
        if "schema" in self.message:
            return self.message["schema"]
        else:
            return []

    def check_version(self):
        if "version" in self.message:
            return self.message["version"]
        else:
            return ""

    def set_update_message(self):
        if self.version != "1.0.0":
            return f"Please upgrade from version {self.version} to version 1.0.0!"
        else:
            return "Thanks for using STAC version 1.0.0!"

    def check_links_assets(self, num_links:int, url_type:str, format_type:str):
        links = []
        if f"{url_type}_validated" in self.message:
            for invalid_request_url in self.message[f"{url_type}_validated"][f"{format_type}_invalid"]:
                if invalid_request_url not in links and 'http' in invalid_request_url:
                    links.append(invalid_request_url)
                num_links = num_links - 1
                if num_links == 0:
                    return links
        return links

    def check_error_type(self):
        if "error_type" in self.message:
            return self.message["error_type"]
        else:
            return ""

    def check_error_message(self):
        if "error_message" in self.message:
            return self.message["error_message"]
        else:
            return ""

    def check_summaries(self):
        if "summaries" in self.data:
            return True
        else:
            return False

    def get_num_links(self):
        if "links" in self.data:
            return len(self.data["links"])
        else:
            return 0

    def return_id(self):
        if "id" in self.data:
            return self.data["id"]
        else:
            return ""

    def get_file_name(self):
        return os.path.basename(self.item).split('.')[0]

    def create_best_practices_msg(self):
        best_practices = list()
        base_string = "STAC Best Practices: "
        best_practices.append(base_string)

        # best practices - item ids should not contain ':' or '/' characters
        if self.asset_type == "ITEM" and "/" in self.object_id or ":" in self.object_id:
            string_1 = f"    Item name '{self.object_id}' should not contain ':' or '/'"
            string_2 = f"    https://github.com/radiantearth/stac-spec/blob/master/best-practices.md#item-ids"
            best_practices.append(string_1)
            best_practices.append(string_2)
            best_practices.append("")

        # best practices - item ids should match file names
        if self.asset_type == "ITEM" and self.object_id != self.file_name:
            string_1 = f"    Item names should match their ids"
            string_2 = f"    '{self.file_name}' not equal to '{self.object_id}'"
            best_practices.append(string_1)
            best_practices.append(string_2)
            best_practices.append("")

        # best practices - collections should contain summaries
        if self.asset_type == "COLLECTION" and self.summaries == False:
            string_1 = f"    A STAC collection should contain a summaries field"
            string_2 = f"    https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md"
            best_practices.append(string_1)
            best_practices.append(string_2)
            best_practices.append("")

        if self.num_links >= 20:
            string_1 = f"    You have {self.num_links} links. Please consider using sub-collections or sub-catalogs"
            string_2 = f"    https://github.com/radiantearth/stac-spec/blob/master/best-practices.md#catalog--collection-practices"
            best_practices.append(string_1)
            best_practices.append(string_2)
            best_practices.append("")

        return best_practices