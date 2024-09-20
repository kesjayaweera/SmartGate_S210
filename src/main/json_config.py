
import json

class JsonConfig:
    """
    Small helper class for reading the different classes from the JSON config

    :param config_path: Path to the config file, in JSON format, containing the rules (default: `../../config/config.json`)
    """
    def __init__(self, config_path='../../config/config.json'):
        #Return dictionary from the JSON configuration file
        with open(self.config_path, 'r') as file:
            self.config = json.load(file)

        #These rules are required
        self.rules_config  = self.config['rules']
        self.server_config = self.config['server']

    def get_rules_config():
        """
        Get the ruleset configuration.
        Example format in JSON:
         "rules": [
            {
                "objects": [...],
                "action": "OPEN"
            },
            {
                "objects": [...],
                "action": "CLOSE"
            }
        ]
        """
        return self.rules_config

    def get_server_config():
        """
        Get the server configuration
        Example format in JSON:
        "server": {
            "port": ...
        }
        """
        return self.server_config

    def update_config(self, new_config, save_to_file=False):
        """Updates the current configuration with new values."""
        self.config.update(new_config)
        if save_to_file:
            self.save_config()

    def save_config(self):
        """Saves the current configuration to the JSON file."""
        with open(self.config_path, 'w') as file:
            json.dump(self.config, file, indent=6)
        