To configure this module please follow the steps below:

1. Make sure you have configured the `queue_job` module, as it is required for background jobs processing.
  - See https://github.com/OCA/queue/tree/18.0/queue_job for instructions.

2. **GitLab Instance Configuration**:
  - Ensure you have access to a GitLab instance (self-hosted or GitLab.com).
  - Create a Personal Access Token (PAT) with the `api` scope.

3. **Odoo Configuration**:
   - Navigate to the GitLab connection settings (Settings > Technical > Gitlab > Connections).
   - Enter the GitLab instance URL and the Personal Token.
   - Test the connection to ensure it is working correctly.

4. **Group Setup**:
    - Create an GitLab group in Odoo (Settings > Technical > Gitlab > Groups).
    - After creating the group you can import subgroups automatically using the "Import Subgroups" button.

5. **Project Setup**:
    - Create an GitLab project in Odoo (Settings > Technical > Gitlab > Projects).
    - Or import projects directly from the linked GitLab group. This is recursive and will import all projects of all subgroups.

6. **Enable Scheduled Actions**:
    - To keep data synchronized, ensure that the scheduled action "Gitlab: Scheduled Import" is enabled (Settings > Technical > Automation > Scheduled Actions). by default, this action is disabled.

7. **Job Queue Channel**:
    - It is recommended to set up a dedicated job queue channel for GitLab synchronization tasks to avoid interference with other background jobs.
