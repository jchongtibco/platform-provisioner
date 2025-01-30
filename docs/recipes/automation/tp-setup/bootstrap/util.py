import os
import sys

from playwright.sync_api import sync_playwright
from color_logger import ColorLogger
from env import ENV
import time
from datetime import datetime
from report import ReportYaml

class Util:
    _browser = None
    _run_start_time = None

    @staticmethod
    def browser_launch(is_headless=ENV.IS_HEADLESS):
        if Util._browser is None:
            Util._run_start_time = time.time()
            playwright = sync_playwright().start()
            Util._browser = playwright.chromium.launch(headless=is_headless)
            ColorLogger.success("Browser Launched Successfully.")

        context = Util._browser.new_context(
            viewport={"width": 2000, "height": 1080},
            ignore_https_errors=True,
            accept_downloads=True
        )

        return context.new_page()

    @staticmethod
    def browser_close():
        if Util._browser is not None:
            Util._browser.close()
            Util._browser = None
            ColorLogger.success("Browser Closed Successfully.")

        if Util._run_start_time is not None:
            ColorLogger.info(f"Total running time: {time.time() - Util._run_start_time:.2f} seconds, current time: {datetime.now().strftime('%m/%d/%Y %H:%M:%S')}")

    @staticmethod
    def screenshot_page(page, filename):
        if filename == "":
            ColorLogger.warning(f"Screenshot filename={filename} MUST be set.")
            return
        attempt_folder = str(ENV.RETRY_TIME)
        screenshot_dir = os.path.join(
            ENV.TP_AUTO_REPORT_PATH,
            attempt_folder,
            "screenshots"
        )
        # check folder screenshot_dir exist or not, if not create it
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir, exist_ok=True)
        file_path = os.path.join(screenshot_dir, filename)
        page.screenshot(path=file_path, full_page=True)
        print(f"Screenshot saved to {file_path}")

    @staticmethod
    def wait_for_success_message(page, timeout=30):
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print("Timeout: Neither success nor error notification appeared.")
                return False

            try:
                if page.locator(".notification-message").is_visible():
                    return True

                if page.locator(".pl-notification--error").is_visible():
                    return False
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                pass
            time.sleep(0.5)

    @staticmethod
    def download_file(file_obj, filename):
        """
        Downloads a file and saves it to the 'dp_commands' directory.

        Args:
            file_obj: The content of the file to be saved. It should have a `save_as` method.
            filename (str): The name of the file to be saved.

        Returns:
            str: The path to the saved file.
        """
        # Create 'dp_commands' folder if it does not exist
        steps_dir = os.path.join(ENV.TP_AUTO_REPORT_PATH, "dp_commands")
        if not os.path.exists(steps_dir):
            os.makedirs(steps_dir, exist_ok=True)
        # Define the full file path
        file_path = os.path.join(steps_dir, filename)
        # Save the file content to the specified path
        file_obj.save_as(file_path)
        print(f"File saved to {file_path}")
        return file_path

    @staticmethod
    def exit_error(message, page=None, filename=""):
        if page is not None:
            Util.screenshot_page(page, f"error-{filename}")
        ColorLogger.error(f"Exiting program: {message}")
        sys.exit(1)

    @staticmethod
    def warning_screenshot(message, page=None, filename=""):
        ColorLogger.warning(message)
        if page is not None:
            Util.screenshot_page(page, f"warning-{filename}")

    @staticmethod
    def refresh_page(page):
        print("Page reload for: ", page.url)
        page.reload()
        page.wait_for_load_state()

    @staticmethod
    def print_env_info(is_print_auth=True, is_print_dp=True):
        ReportYaml.set(".ENV.CP_MAIL_URL", ENV.TP_AUTO_MAIL_URL)
        ReportYaml.set(".ENV.CP_ADMIN_URL", ENV.TP_AUTO_ADMIN_URL)
        ReportYaml.set(".ENV.CP_ADMIN_USER", ENV.CP_ADMIN_EMAIL)
        ReportYaml.set(".ENV.CP_ADMIN_PASSWORD", ENV.CP_ADMIN_PASSWORD)
        ReportYaml.set(".ENV.CP_URL", ENV.TP_AUTO_LOGIN_URL)
        ReportYaml.set(".ENV.CP_USER", ENV.DP_USER_EMAIL)
        ReportYaml.set(".ENV.CP_PASSWORD", ENV.DP_USER_PASSWORD)
        ReportYaml.set(".ENV.ELASTIC_URL", ENV.TP_AUTO_ELASTIC_URL)
        ReportYaml.set(".ENV.KIBANA_URL", ENV.TP_AUTO_KIBANA_URL)
        ReportYaml.set(".ENV.ELASTIC_USER", ENV.TP_AUTO_ELASTIC_USER)
        ReportYaml.set(".ENV.ELASTIC_PASSWORD", ENV.TP_AUTO_ELASTIC_PASSWORD)
        ReportYaml.set(".ENV.PROMETHEUS_URL", ENV.TP_AUTO_PROMETHEUS_URL)
        ReportYaml.set(".ENV.PROMETHEUS_USER", ENV.TP_AUTO_PROMETHEUS_USER)
        ReportYaml.set(".ENV.PROMETHEUS_PASSWORD", ENV.TP_AUTO_PROMETHEUS_PASSWORD)
        str_num = 90
        col_space = 28
        print("=" * str_num)
        if is_print_auth:
            print("-" * str_num)
            print(f"{'Login Credentials': ^{str_num}}")
            print("-" * str_num)
            print(f"{'Mail URL:':<{col_space}}{ENV.TP_AUTO_MAIL_URL}")
            print("-" * str_num)
            print(f"{'CP Admin URL:':<{col_space}}{ENV.TP_AUTO_ADMIN_URL}")
            print(f"{'Admin Email:':<{col_space}}{ENV.CP_ADMIN_EMAIL}")
            print(f"{'Admin Password:':<{col_space}}{ENV.CP_ADMIN_PASSWORD}")
            print("-" * str_num)
            print(f"{'CP Login URL:':<{col_space}}{ENV.TP_AUTO_LOGIN_URL}")
            print(f"{'User Email:':<{col_space}}{ENV.DP_USER_EMAIL}")
            print(f"{'User Password:':<{col_space}}{ENV.DP_USER_PASSWORD}")
        if is_print_dp:
            print("-" * str_num)
            print(f"{'Elastic/Kibana/Prometheus Credentials': ^{str_num}}")
            print("-" * str_num)
            print(f"{'Elastic URL:':<{col_space}}{ENV.TP_AUTO_ELASTIC_URL}")
            print(f"{'Kibana URL:':<{col_space}}{ENV.TP_AUTO_KIBANA_URL}")
            print(f"{'User Name:':<{col_space}}{ENV.TP_AUTO_ELASTIC_USER}")
            print(f"{'User Password:':<{col_space}}{ENV.TP_AUTO_ELASTIC_PASSWORD}")
            print("-" * str_num)
            print(f"{'Prometheus URL:':<{col_space}}{ENV.TP_AUTO_PROMETHEUS_URL}")
            if ENV.TP_AUTO_PROMETHEUS_USER != "":
                print(f"{'User Name:':<{col_space}}{ENV.TP_AUTO_PROMETHEUS_USER}")
            if ENV.TP_AUTO_PROMETHEUS_PASSWORD != "":
                print(f"{'User Password:':<{col_space}}{ENV.TP_AUTO_PROMETHEUS_PASSWORD}")
            print("-" * str_num)
            dp_names = ReportYaml.get_dataplanes()
            if len(dp_names) > 0:
                print(f"{'Data Plane, App': ^{str_num}}")
                print("-" * str_num)
                for dp_name in dp_names:
                    print(f"{'DataPlane Name:':<{col_space}}{dp_name}")

                    is_config_o11y = ReportYaml.get_dataplane_info(dp_name, "o11yConfig")
                    if is_config_o11y == "True":
                        print(f"{'DataPlane Configured:':<{col_space}}{is_config_o11y}")

                    dp_capabilities = ReportYaml.get_capabilities(dp_name)
                    if len(dp_capabilities) > 0:
                        print(f"{'Provisioned capabilities:':<{col_space}}"
                              f"{[cap.upper() for cap in dp_capabilities]}"
                              )

                    for dp_capability in dp_capabilities:
                        app_names = ReportYaml.get_capability_apps(dp_name, dp_capability)
                        if len(app_names) > 0:
                            print(f"{dp_capability.capitalize()}")

                        for app_name in app_names:
                            app_status = ReportYaml.get_capability_app_info(dp_name, dp_capability, app_name, "status")
                            print(f"{'  App Name:':<{col_space}}{app_name}")
                            if app_status:
                                print(f"{'  App Status:':<{col_space}}{app_status}")
        print("=" * str_num)

    @staticmethod
    def check_dom_visibility(page, dom_selector, interval=10, max_wait=180, is_refresh=False):
        total_attempts = max_wait // interval
        timeout = interval if interval < 5 else 5
        print(f"Check dom visibility, wait {timeout} seconds first, then loop to check")
        page.wait_for_timeout(timeout * 1000)
        for attempt in range(total_attempts):
            if dom_selector.is_visible():
                print("Dom is now visible.")
                return True

            print(f"--- Attempt {attempt + 1}/{total_attempts}, Loop to check: Checking if dom is visible...")
            if attempt <= total_attempts - 1:
                if is_refresh:
                    print(f"Page reload {attempt + 1}")
                    Util.refresh_page(page)
                print(f"Dom not visible. Waiting for {interval} seconds before retrying...")
                page.wait_for_timeout(interval * 1000)

        ColorLogger.warning(f"Dom is still not visible after waiting for {max_wait} seconds.")
        return False

    @staticmethod
    def click_button_until_enabled(page, button_selector):
        button_selector.wait_for(state="visible")
        page.wait_for_function(
            """
            (button) => !button.disabled
            """,
            arg=button_selector.element_handle()
        )
        button_selector.click()
