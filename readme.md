# PCG API Script Notice – Release 25r3

_The software is provided as-is and [Extreme Networks](http://www.extremenetworks.com/) has no obligation to provide maintenance, support, updates, enhancements, or modifications. Any support provided by [Extreme Networks](http://www.extremenetworks.com/) is at its sole discretion._

_Issues and/or bug fixes may be reported on in the Issues for this repository._

### ✅ PCG API Update Now Available

The **25r3 release** has introduced **pagination** to the PCG API, aligning it with other APIs like PPSK. This change allows users to retrieve data in pages (e.g., 100 users at a time) for improved performance.

#### What This Means for You

If you're using an older script to interact with the PCG API, **it will no longer work correctly** with the 25r3 release.

#### Required Action

The updated script (**v1.3.0**) is now available and supports pagination. To ensure uninterrupted functionality:

1. **Download v1.3.0**: Get the new script version from the API portal or repository.
2. **Copy Variables**: Transfer your existing variables (e.g., API keys, endpoints) from your old script to the new v1.3.0 script.
3. **Test Your Script**: Verify that the updated script retrieves all users as expected with the new pagination logic.

---

Thank you for updating promptly to keep your workflows running smoothly! For detailed usage instructions or support, refer to the documentation or contact support.
