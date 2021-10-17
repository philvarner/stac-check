from stac_validator import stac_validator

class Linter:
    def __init__(
        self, 
        item = str
    ):
        self.item = item
        self.version = ""
        self.message = self.validate_file(self.item)
        self.validator_version = "2.3.0"
        self.schema = []
        self.update_msg = ""
        self.asset_type = ""
        self.valid_stac = False

    def parse_file(self):
        self.check_version()
        self.schema = self.message["schema"]
        self.asset_type = self.message["asset_type"]
        self.valid_stac = self.message["valid_stac"]
        return self.message
 
    def check_version(self):
        self.version = self.message["version"]
        if self.message["valid_stac"] and self.version != "1.0.0":
            self.update_msg = f"Please upgrade from version {self.version} to version 1.0.0!"
        else:
            self.update_msg = "Thanks for using STAC version 1.0.0!"

    def validate_file(self, file):
        stac = stac_validator.StacValidate(file)
        stac.run()
        return stac.message[0]

    