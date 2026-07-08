# PCG API Script Notice – July 2026

_The software is provided as-is and [Extreme Networks](http://www.extremenetworks.com/) has no obligation to provide maintenance, support, updates, enhancements, or modifications. Any support provided by [Extreme Networks](http://www.extremenetworks.com/) is at its sole discretion._

_Issues and/or bug fixes may be reported on in the Issues for this repository._

### ⚠️ Current Known Issue (Under Investigation)

**When PCG is enabled**, customers are currently experiencing significant slowness when creating or deleting PCG users.  
This issue **only affects environments where PCG is enabled** and does **not** occur when PCG is disabled.

Our engineering team is actively investigating the root cause and working on a permanent fix. We'll keep you updated on progress and resolution timeline.

**For PCG-enabled environments:** Use the updated script from the PCG-Bulk branch at https://github.com/ExtremeNetworksSA/XIQ_Gsuite_PPSK_Sync/tree/PCG-Bulk. This branch includes batch import/delete operations and retry logic to mitigate timeouts (up to 10 attempts before skipping users).

**Required Action**
The updated script (v3.0.1) is now available in the PCG-Bulk branch and includes bulk PCG support. 

To ensure uninterrupted functionality:

Download v3.0.1: Get the new script version from the PCG-Bulk branch if using PCG.
* This is a new version of the script. all files should be replaced with the new files and follow the new documentation included in the branch.

Copy Variables: Transfer your existing variables (e.g., endpoints) from your old script to the new version.
Generate a new token: A new token will need to be generated to include the lro permission for the long-running operation
Test Your Script: Verify that the updated script retrieves all users as expected with the new pagination logic.


If PCG is not enabled: You can continue using v1.3.0 without changes.

Thank you for your patience while we resolve the performance issue with PCG user create/delete operations.