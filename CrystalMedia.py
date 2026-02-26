class FixedProgressLogger:
    def __init__(self):
        # Assuming this is where border styles are set
        self.progress_panel_border_style = 'COL_MENU'  # Changed from 'green'
        self.log_panel_border_style = 'COL_MENU'  # Changed from 'blue'

    def update_progress(self, current, total):
        percent_complete = (current / total) * 100
        # Here we format the log message to show better info
        log_message = f"Progress: {current} of {total} ({percent_complete:.2f}%)"
        print(log_message)  # Adjust with your logging setup if necessary
        
    # Assuming there are methods around lines 306-308 and 345
    def display_progress(self):
        # ... your existing code... 
        # Update progress section
        self.progress_panel_border_style = 'COL_MENU'  # Use COL_MENU for the panel style
        # Update the display for log panel
        self.log_panel_border_style = 'COL_MENU'  # Use COL_MENU for the log style
        # ... remaining code... 
