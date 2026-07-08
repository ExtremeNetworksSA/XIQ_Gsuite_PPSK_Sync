

_The software is provided as-is and [Extreme Networks](http://www.extremenetworks.com/) has no obligation to provide maintenance, support, updates, enhancements, or modifications. Any support provided by [Extreme Networks](http://www.extremenetworks.com/) is at its sole discretion._

_Issues and/or bug fixes may be reported on in the Issues for this repository._

# PCG API Script Notice – Release 25r3

### ✅ PCG API Update Now Available

The **25r3 release** has introduced **pagination** to the PCG API, aligning it with other APIs like PPSK. This change allows users to retrieve data in pages (e.g., 100 users at a time) for improved performance.

#### ⚠️ Current Known Issue (Under Investigation)

**When PCG is enabled**, customers are currently experiencing significant slowness when creating or deleting PCG users.  
This issue **only affects environments where PCG is enabled** and does **not** occur when PCG is disabled.

**Updates to mitigate slowness and deletion timeouts**  
To address this, the updated script (v3.0.1) now uses batch import and batch delete operations for PCG users when PCG is enabled. We've also added automatic retries—up to 10 attempts— for delete operations before skipping affected users. This should resolve most failures without manual intervention.

**Specific impact on user deletion**
In previous versions, deleting a user could fail if the PCG deletion was still processing when the script attempted the associated PPSK deletion. With v3.0.1's retries and batch handling, these scenarios are significantly reduced, though rare timeouts may still occur.

Our engineering team is actively investigating the root cause of the slowness and working on a permanent fix. We’ll keep you updated on progress and resolution timeline.

#### Required Action

The updated script (**v3.0.1**) is now available and supports pagination. To ensure uninterrupted functionality:

1. **Download v3.0.1**: Get the new script version from the API portal or repository.
2. **Copy Variables**: Transfer your existing variables (e.g., endpoints) from your old script to the new v2.1.0 script.
3. **Generate new token**: Follow guide to generate a new token with the lro permission included.
3. **Test Your Script**: Verify that the updated script retrieves all users as expected with the new pagination logic.

Thank you for your patience while we resolve the performance issue with PCG user create/delete operations.


#### Release Notes
v3.0.0 is a major update to the script. In addition to the PCG Batch changes other changes where made. There is a new **/app/** folder with 2 scripts included that must be in the same folder with the main **XIQ-GSuite-PPSK-Sync.py** script. 
v3.0.1 is an update to documentation and comment in the script. The token needs the lro permission to check the status of the long-running operation when creating PCG users in bulk.
##### Other Changes
1. **logging**: additional logging has been added. 
a. Main logging function moved to logger.py script in app folder
b. logs will be saved to XIQ-GSuite-PPSK-sync.log file in an automatically created 'script_logs' folder inside of the app folder
c. log rotation added - logs will rotate at 5GB and backup up to 5 files.
2. **XIQ APIs**: the APIs have been moved out of the main script and into the xiq_api.py script inside of the app folder.
