# PCG API Script Notice – July 2026

_The software is provided as-is and [Extreme Networks](http://www.extremenetworks.com/) has no obligation to provide maintenance, support, updates, enhancements, or modifications. Any support provided by [Extreme Networks](http://www.extremenetworks.com/) is at its sole discretion._
<<<<<<< HEAD

_Issues and/or bug fixes may be reported on in the Issues for this repository._

### ✅ PCG API Update Now Available
=======
>>>>>>> 095a155 (readme update for PCG)

_Issues and/or bug fixes may be reported on in the Issues for this repository._

<<<<<<< HEAD
#### ⚠️ Current Known Issue (Under Investigation)

**When PCG is enabled**, customers are currently experiencing significant slowness when creating or deleting PCG users.  
This issue **only affects environments where PCG is enabled** and does **not** occur when PCG is disabled.

**Specific impact on user deletion**  
When deleting a user, the script attempts to delete the PCG user first and then immediately delete the associated PPSK user.  
Because of the current backend slowness with PCG user deletion, the PCG delete may still be in progress when the script attempts the PPSK delete → this causes the PPSK deletion to fail with an error.

**Recommended workaround for deletion failures**  
Simply re-run the script after waiting ~30–60 seconds. By the second run, the PCG user deletion will have completed, and the script will successfully delete the remaining PPSK user(s) without error.

Our engineering team is actively investigating the root cause of the slowness and working on a permanent fix. We’ll keep you updated on progress and resolution timeline.

#### What the Pagination Change Means for You
=======
### ⚠️ Current Known Issue (Under Investigation)
>>>>>>> 095a155 (readme update for PCG)

**When PCG is enabled**, customers are currently experiencing significant slowness when creating or deleting PCG users.  
This issue **only affects environments where PCG is enabled** and does **not** occur when PCG is disabled.

Our engineering team is actively investigating the root cause and working on a permanent fix. We'll keep you updated on progress and resolution timeline.

<<<<<<< HEAD
The updated script (**v2.1.0**) is now available and supports pagination. To ensure uninterrupted functionality:

1. **Download v2.1.0**: Get the new script version from the API portal or repository.
2. **Copy Variables**: Transfer your existing variables (e.g., API keys, endpoints) from your old script to the new v2.1.0 script.
3. **Test Your Script**: Verify that the updated script retrieves all users as expected with the new pagination logic.

=======
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

>>>>>>> 095a155 (readme update for PCG)
Thank you for your patience while we resolve the performance issue with PCG user create/delete operations.