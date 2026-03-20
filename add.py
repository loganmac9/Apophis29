class AddNum:
    def __init__(self, config, logger):
        """Initialize AddNum class with config and logger"""
        self.config = config
        self.logger = logger

        # Set default values
        default_num1 = 2
        default_num2 = 4
        self.sum = None

        # Try to get values from config, create them if they don't exist
        config_num1 = self.config.get_value('num1')
        if config_num1 is None:
            # Create the config entry with default value
            self.config.create_key_value('num1', str(default_num1), "First number for AddNum class")
            self.num1 = default_num1
            self.logger.info(f"Created config entry num1 with default value: {default_num1}")
        else:
            self.num1 = int(config_num1)
            self.logger.info(f"Loaded num1 from config: {self.num1}")

        config_num2 = self.config.get_value('num2')
        if config_num2 is None:
            # Create the config entry with default value
            self.config.create_key_value('num2', str(default_num2), "Second number for AddNum class")
            self.num2 = default_num2
            self.logger.info(f"Created config entry num2 with default value: {default_num2}")
        else:
            self.num2 = int(config_num2)
            self.logger.info(f"Loaded num2 from config: {self.num2}")

        self.logger.info(f"AddNum class initialized with numbers: {self.num1}, {self.num2}")
        
    def add(self):
        """Add the two numbers"""
        self.sum = self.num1 + self.num2
        self.logger.info(f"Addition performed: {self.num1} + {self.num2} = {self.sum}")
    
    def printNum(self):
        """Print the numbers and their sum"""
        print("Number1 is: ", self.num1)
        print("Number2 is: ", self.num2)
        print("The two numbers add to become: ", self.sum)
        self.logger.info(f"Results displayed - Sum: {self.sum}")