from utils.color_logger import ColorLogger
from utils.util import Util
from utils.helper import Helper
from utils.env import ENV
from utils.report import ReportYaml

class PageObjectDataPlane:
    def __init__(self, page):
        self.page = page
        self.env = ENV

    def goto_left_navbar(self, item_name):
        ColorLogger.info(f"Going to left side menu ...")
        self.page.locator(".nav-bar-pointer", has_text=item_name).wait_for(state="visible")
        self.page.locator(".nav-bar-pointer", has_text=item_name).click()
        print(f"Clicked left side menu '{item_name}'")
        self.page.wait_for_timeout(500)

    def goto_left_navbar_dataplane(self):
        self.goto_left_navbar("Data Planes")
        self.page.locator(".data-planes-content").wait_for(state="visible")
        print(f"Waiting for Data Planes page is loaded")

    def goto_global_dataplane(self):
        ColorLogger.info(f"Going to Global Data Plane...")
        self.page.click("#nav-bar-menu-list-dataPlanes")
        # wait for 1 seconds
        self.page.wait_for_timeout(1000)

        self.page.locator(".global-configuration button").click()
        print("Clicked 'Global configuration' button")
        self.page.locator('.global-configuration breadcrumbs a', has_text="Global configuration").wait_for(state="visible")
        print(f"Navigated to Global Data Plane page")

    def goto_dataplane(self, dp_name):
        ColorLogger.info(f"Going to k8s Data Plane '{dp_name}'...")
        self.page.click("#nav-bar-menu-list-dataPlanes")
        self.page.wait_for_timeout(2000)
        is_dataplane_visible = Util.refresh_until_success(self.page,
                                                          self.page.locator('.data-plane-name', has_text=dp_name),
                                                          self.page.locator(".data-planes-content"),
                                                          "DataPlane list page is load.")

        if is_dataplane_visible:
            self.page.locator('data-plane-card', has=self.page.locator('.data-plane-name', has_text=dp_name)).locator('button', has_text="Go to Data Plane").click()
            print("Clicked 'Go to Data Plane' button")
            self.page.wait_for_timeout(2000)
            is_dataplane_detail_visible = Util.refresh_until_success(self.page,
                                                                     self.page.locator('.domain-data-title', has_text=dp_name),
                                                                     self.page.locator('.domain-data-title', has_text=dp_name),
                                                                     f"DataPlane '{dp_name}' detail page is load.")
            if is_dataplane_detail_visible:
                print(f"Navigated to Data Plane '{dp_name}' detail page")
                self.page.wait_for_timeout(1000)
            else:
                Util.exit_error(f"DataPlane {dp_name} detail page is not load.", self.page, "goto_dataplane.png")

        else:
            Util.exit_error(f"DataPlane {dp_name} does not exist", self.page, "goto_dataplane.png")

    def goto_capability(self, dp_name, capability, is_check_status=True):
        ColorLogger.info(f"{capability} Going to capability...")
        self.goto_dataplane(dp_name)
        print(f"Check if {capability} capability is ready...")
        card_id = capability.lower()
        if Util.check_dom_visibility(self.page, self.page.locator(f"capability-card #{card_id}"), 10, 120, True):
            print(f"Waiting for {capability} capability status is ready...")
            is_capability_success = Util.check_dom_visibility(self.page, self.page.locator(f"capability-card #{card_id} .status .success"))
            if not is_check_status or is_capability_success:
                self.page.locator(f"capability-card #{card_id} .image-name").click()
                print(f"Clicked '{capability}' capability")
                self.page.wait_for_timeout(3000)
                if not is_check_status:
                    print(f"Ignore check '{capability}' capability status, get into '{capability}' capability page")
                if is_capability_success:
                    print(f"{capability} capability status is ready")

                is_capability_loaded = Util.refresh_until_success(self.page,
                                                                  self.page.locator(".capability-connectors-container .total-capability"),
                                                                  self.page.locator(".capability-connectors-container .total-capability"),
                                                                  f"{capability} capability detail page is loaded")
                if is_capability_loaded:
                    print(f"Navigated to {capability} capability detail page")
                    self.page.wait_for_timeout(1000)
                else:
                    Util.exit_error(f"{capability} capability page is not loaded.", self.page, f"{card_id}_goto_capability.png")
            else:
                Util.exit_error(f"{capability} capability is provisioned, but status is not ready.", self.page, f"{card_id}_goto_capability.png")
        else:
            Util.exit_error(f"{capability} capability is not provisioned yet.", self.page, f"{card_id}_goto_capability.png")

    def goto_app_detail(self, dp_name, app_name):
        ColorLogger.info(f"Going to app '{app_name}' detail page")
        self.goto_dataplane(dp_name)
        is_app_visible = Util.refresh_until_success(self.page,
                                                    self.page.locator("apps-list td.app-name a", has_text=app_name),
                                                    self.page.locator("apps-list td.app-name a", has_text=app_name),
                                                    "App detail page is load.")
        if is_app_visible:
            self.page.locator("apps-list td.app-name a", has_text=app_name).click()
            print(f"Clicked app '{app_name}'")
            self.page.locator(".app-name-section .name", has_text=app_name).wait_for(state="visible")
            print(f"Navigated to app '{app_name}' detail page")
            self.page.wait_for_timeout(500)
        else:
            Util.exit_error(f"The app '{app_name}' is not deployed yet.", self.page, "goto_app_detail.png")

    def is_capability_provisioned(self, capability, capability_name=""):
        ColorLogger.info(f"Checking if '{capability}' is provisioned")
        try:
            print(f"Checking if '{capability}' is already provisioned...")
            card_id = capability.lower()
            self.page.wait_for_timeout(3000)
            if self.page.locator(f"capability-card #{card_id}").is_visible():
                ColorLogger.success(f"'{capability}' is already provisioned.")
                if capability_name == "":
                    return True
                else:
                    if self.page.locator(f"capability-card #{card_id} .pl-tooltip__trigger", has_text=capability_name).is_visible():
                        ColorLogger.success(f"'{capability}' with name '{capability_name}' is provisioned.")
                        return True
                    else:
                        ColorLogger.warning(f"'{capability}' with name '{capability_name}' has not been provisioned.")
                        return False
            else:
                ColorLogger.warning(f"'{capability}' has not been provisioned.")
                return False
        except Exception as e:
            ColorLogger.warning(f"An error occurred while Checking capability '{capability}': {e}")
            return False

    def k8s_delete_dataplane(self, dp_name):
        ColorLogger.info(f"Deleting Data Plane '{dp_name}'")
        self.goto_left_navbar_dataplane()

        is_dataplane_visible = Util.refresh_until_success(self.page,
                                                          self.page.locator('.data-plane-name', has_text=dp_name),
                                                          self.page.locator(".data-planes-content"),
                                                          "DataPlane list page is load.")

        if is_dataplane_visible:
            self.page.locator('data-plane-card', has=self.page.locator('.data-plane-name', has_text=dp_name)).locator('.delete-dp-dropdown button').nth(0).click()
            print(f"Clicked '⋮' icon in Data Plane {dp_name} card")
            self.page.locator(".is-shown .pl-dropdown-menu__action", has_text="Delete Data Plane").nth(0).wait_for(state="visible")
            self.page.locator(".is-shown .pl-dropdown-menu__action", has_text="Delete Data Plane").nth(0).click()
            print(f"Clicked 'Delete Data Plane' menu item")
            self.page.locator(".delete-dp-modal").wait_for(state="visible")
            print("'Delete Data Plane' dialog popup.")
            self.page.locator(".delete-dp-modal #confirm-button").click()
            if Util.wait_for_success_message(self.page, 5):
                print("'Delete Data Plane' success message is displayed.")
                self.page.locator('.data-plane-name', has_text=dp_name).wait_for(state="detached")
                ColorLogger.success(f"Deleted Data Plane '{dp_name}'")

    def k8s_create_dataplane(self, dp_name, retry=0):
        if ReportYaml.is_dataplane_created(dp_name):
            ColorLogger.success(f"In {ENV.TP_AUTO_REPORT_YAML_FILE} file, DataPlane '{dp_name}' is already created.")
            return

        ColorLogger.info(f"Creating k8s Data Plane '{dp_name}'...")
        self.page.wait_for_timeout(2000)

        if self.page.locator(".data-plane-name").count() > ENV.TP_AUTO_MAX_DATA_PLANE:
            Util.exit_error("Too many data planes, please delete some data planes first.", self.page, "k8s_create_dataplane.png")

        if self.page.locator('.data-plane-name', has_text=dp_name).is_visible():
            ReportYaml.set_dataplane(dp_name)
            ColorLogger.success(f"DataPlane '{dp_name}' is already created.")
            return

        self.page.click("#register-dp-button")
        self.page.locator("#select-existing-dp-button").wait_for(state="visible")
        self.page.click("#select-existing-dp-button")
        # step 1 Basic
        print("Waiting for Step 1: 'Basic' page is loaded")
        self.page.locator(".pl-secondarynav a.is-active", has_text="Basic").wait_for(state="visible")
        self.page.fill("#data-plane-name-text-input", dp_name)
        print(f"Input Data Plane Name: {dp_name}")
        self.page.locator('label[for="eua-checkbox"]').click()
        self.page.click("#data-plane-basics-btn")
        print("Clicked Next button, Finish step 1 Basic")

        # step 2 Namespace & Service account
        print("Waiting for Step 2: 'Namespace & Service account' page is loaded")
        self.page.locator(".pl-secondarynav a.is-active", has_text="Namespace & Service account").wait_for(state="visible")
        self.page.fill("#namespace-text-input", ENV.TP_AUTO_K8S_DP_NAMESPACE)
        print(f"Input NameSpace: {ENV.TP_AUTO_K8S_DP_NAMESPACE}")
        self.page.fill("#service-account-text-input", ENV.TP_AUTO_K8S_DP_SERVICE_ACCOUNT)
        print(f"Input Service Account: {ENV.TP_AUTO_K8S_DP_SERVICE_ACCOUNT}")
        self.page.click("#data-plane-namespace-btn")
        print("Clicked Next button, Finish step 2 Namespace & Service account")

        # step 3 Configuration
        print("Waiting for Step 3: 'Configuration' page is loaded")
        self.page.locator(".pl-secondarynav a.is-active", has_text="Configuration").wait_for(state="visible")
        # use global repository, no need below code
        # if page.locator('label[for="helm-chart-repo-global"]').is_visible():
        #     if ENV.GITHUB_TOKEN == "":
        #         print("GITHUB_TOKEN is empty, choose 'Global Repository'")
        #         page.locator('label[for="helm-chart-repo-global"]').click()
        #     else:
        #         print("GITHUB_TOKEN is set, choose 'Custom Helm Chart Repository'")
        #         if page.locator('label[for="helm-chart-repo-custom"]').is_visible():
        #             page.locator('label[for="helm-chart-repo-custom"]').click()
        #             print("Choose 'Custom Helm Chart Repository'")
        #
        #
        #         page.fill("#alias-input", f"tp-private-{dp_name}")
        #         print(f"Input Repository Alias: tp-private-{dp_name}")
        #         page.fill("#url-input", "https://raw.githubusercontent.com")
        #         print("Input Registry URL: https://raw.githubusercontent.com")
        #         page.fill("#repo-input", "tibco/tp-helm-charts/gh-pages")
        #         print("Input Repository: tibco/tp-helm-charts/gh-pages")
        #         page.fill("#username-input", "cp-test")
        #         print("Input Username: cp-test")
        #         page.fill("#password-input", ENV.GITHUB_TOKEN)
        #         print(f"Input Password: {ENV.GITHUB_TOKEN}")

        self.page.click("#data-plane-config-btn")
        print("Clicked Next button, Finish step 3 Configuration")

        # step Preview (for 1.4 and above)
        if Util.check_dom_visibility(self.page, self.page.locator(".pl-secondarynav a.is-active", has_text="Preview"), 3, 9):
            print("Step 4: 'Preview' page is loaded")
            self.page.wait_for_timeout(1000)
            if self.page.locator("#data-plane-preview-btn").is_visible():
                self.page.click("#data-plane-preview-btn")
                print("Clicked Next button, Finish step 4 Preview")

        # step Register Data Plane
        print("Check if create Data Plane is successful...")
        if not Util.check_dom_visibility(self.page, self.page.locator(".register-data-plane-content"), 3, 45):
            self.k8s_delete_dataplane(dp_name)
            if retry >= 3:
                Util.exit_error(f"Data Plane '{dp_name}' creation failed.", self.page, "k8s_create_dataplane_finish.png")

            ColorLogger.warning(f"Data Plane '{dp_name}' creation failed, retry {retry + 1} times.")
            self.k8s_create_dataplane(dp_name, retry + 1)

        download_commands = self.page.locator("#download-commands")
        commands_title = self.page.locator(".register-data-plane p.title").all_text_contents()
        print("commands_title:", commands_title)

        # Execute each command dynamically based on its position
        for index, step_name in enumerate(commands_title):
            self.k8s_run_dataplane_command(dp_name, step_name, download_commands.nth(index), index + 1)

        # click Done button
        self.page.click("#data-plane-finished-btn")
        print("Data Plane create successful, clicked 'Done' button")
        ReportYaml.set_dataplane_info(dp_name, "runCommands", True)
        self.page.locator('#confirm-button', has_text="Yes").wait_for(state="visible")
        self.page.locator('#confirm-button', has_text="Yes").click()

        # verify data plane is created in the list
        self.page.wait_for_timeout(2000)
        print(f"Verifying Data Plane {dp_name} is created in the list")
        self.k8s_wait_tunnel_connected(dp_name)

    def k8s_run_dataplane_command(self, dp_name, step_name, download_selector, step):
        ColorLogger.info(f"Running command for: {step_name}")
        print(f"Download: {step_name}")
        with self.page.expect_download() as download_info:
            download_selector.click()

        file_name = f"{dp_name}_{step}.sh"
        file_path = Util.download_file(download_info.value, file_name)

        print(f"Run command for: {step_name}")
        Helper.run_shell_file(file_path)
        print(f"Command for step: {step_name} is executed, wait for 3 seconds.")
        self.page.wait_for_timeout(3000)

    def k8s_wait_tunnel_connected(self, dp_name):
        print(f"Waiting for Data Planes {dp_name} tunnel connected.")
        self.goto_left_navbar_dataplane()
        print(f"Navigated to Data Planes list page, and checking for {dp_name} in created and tunnel connected.")
        self.page.locator('.data-plane-name', has_text=dp_name).wait_for(state="visible")
        if not self.page.locator('.data-plane-name', has_text=dp_name).is_visible():
            Util.exit_error(f"DataPlane {dp_name} is not created.", self.page, "k8s_wait_tunnel_connected_1.png")

        ColorLogger.success(f"DataPlane {dp_name} is created, waiting for tunnel connected.")
        ReportYaml.set_dataplane(dp_name)
        data_plane_card = self.page.locator(".data-plane-card", has=self.page.locator('.data-plane-name', has_text=dp_name))
        print(f"Waiting for DataPlane {dp_name} tunnel connected...")
        if not Util.check_dom_visibility(self.page, data_plane_card.locator('.tunnel-status svg.green'), 10, 180):
            Util.exit_error(f"DataPlane {dp_name} tunnel is not connected, exit program and recheck again.", self.page, "k8s_wait_tunnel_connected_2.png")

        ColorLogger.success(f"DataPlane {dp_name} tunnel is connected.")
        ReportYaml.set_dataplane_info(dp_name, "tunnelConnected", True)

    # below functions will move to po_dp_{capability}.py



