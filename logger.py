import os
import sys
import time
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    """Enum for log levels"""
    ERROR = 1
    INFO = 2
    DEBUG = 3
    TRACE = 4

class Logger:
    def __init__(self, config_manager):
        """Initialize Logger with ConfigManager"""
        self.config = config_manager
        
        # Get configuration settings
        self.log_file = self.config.get_value('log_file_path')
        self.write_to_file = self.config.get_value('write_to_file').lower() == 'true'
        self.write_to_console = self.config.get_value('write_to_console').lower() == 'true'
        self.log_level = LogLevel[self.config.get_value('log_level').upper()]
        
        # Create log directory if it doesn't exist
        if self.write_to_file and self.log_file:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def write(self, level, message):
        """Write a message to the log"""
        if not isinstance(level, LogLevel):
            level = LogLevel[level.upper()]
            
        # Only log if the message level is less than or equal to configured level
        if level.value <= self.log_level.value:
            # Create the log entry
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            pid = os.getpid()
            log_entry = f"[{timestamp}] [{pid}] [{level.name}] {message}"
            
            # Write to console if enabled
            if self.write_to_console:
                if level == LogLevel.ERROR:
                    print(log_entry, file=sys.stderr)
                else:
                    print(log_entry)
            
            # Write to file if enabled
            if self.write_to_file and self.log_file:
                try:
                    with open(self.log_file, 'a') as file:
                        file.write(log_entry + '\n')
                except Exception as e:
                    print(f"Error writing to log file: {str(e)}", file=sys.stderr)

    def error(self, message):
        """Convenience method for ERROR level logs"""
        self.write(LogLevel.ERROR, message)

    def info(self, message):
        """Convenience method for INFO level logs"""
        self.write(LogLevel.INFO, message)

    def debug(self, message):
        """Convenience method for DEBUG level logs"""
        self.write(LogLevel.DEBUG, message)

    def trace(self, message):
        """Convenience method for TRACE level logs"""
        self.write(LogLevel.TRACE, message)

"""
# All  goes into the main
# Example usage:
if __name__ == "__main__":
    from config_manager import ConfigManager
    
    # Create and setup config
    config = ConfigManager("settings.conf")
    
    # Set up logging configuration
    config.create_key_value("log_file_path", "logs/application.log", "Log file location")
    config.create_key_value("write_to_file", "true", "Enable/disable file logging")
    config.create_key_value("write_to_console", "true", "Enable/disable console logging")
    config.create_key_value("log_level", "DEBUG", "Logging level (ERROR, INFO, DEBUG, TRACE)")
    
    # Create logger instance
    logger = Logger(config)
    
    # Example log messages
    logger.error("This is an error message")
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    logger.trace("This won't show unless log_level is TRACE")
    
    # Alternative syntax
    logger.write("ERROR", "Another error message")
    logger.write(LogLevel.INFO, "Another info message")
"""