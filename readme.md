# PCG API Script Notice – Release 25r3

_The software is provided as-is and [Extreme Networks](http://www.extremenetworks.com/) has no obligation to provide maintenance, support, updates, enhancements, or modifications. Any support provided by [Extreme Networks](http://www.extremenetworks.com/) is at its sole discretion._

_Issues and/or bug fixes may be reported on in the Issues for this repository._

### ✅ PCG API Update Now Available

The **25r3 release** has introduced **pagination** to the PCG API, aligning it with other APIs like PPSK. This change allows users to retrieve data in pages (e.g., 100 users at a time) for improved performance.

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

If you're using an older script to interact with the PCG API, **it will no longer work correctly** with the 25r3 release.

#### Required Action

The updated script (**v2.1.0**) is now available and supports pagination. To ensure uninterrupted functionality:

1. **Download v2.1.0**: Get the new script version from the API portal or repository.
2. **Copy Variables**: Transfer your existing variables (e.g., API keys, endpoints) from your old script to the new v2.1.0 script.
3. **Test Your Script**: Verify that the updated script retrieves all users as expected with the new pagination logic.

Thank you for your patience while we resolve the performance issue with PCG user create/delete operations.