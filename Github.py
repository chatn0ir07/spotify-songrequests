import json
import requests



class Github:
    TARGETURL = "https://api.github.com/repos/[u]/[r]/[a]"
    def __init__(self, username, repository, ReleaseTag = 1):
        self.User = username
        self.Repo = repository
        self.Tag = ReleaseTag
    def CheckReleases(self):
        requestObj = requests.get(Github.TARGETURL.replace("[u]", self.User).replace("[r]", self.Repo).replace("[a]", "releases"))
        activity = json.loads(requestObj.text)
        if len(activity) == 0:
            return {"IsNew": False}
        #Check if newest release has higher different Tagname than current version
        if activity[0]["tag_name"] != str(self.Tag):
            return {"IsNew": True, "ID": activity[0]["id"],"Tarball_URL": activity[0]["tarball_url"], "Zipball_URL": activity[0]["zipball_url"]}
        else:
            return {"IsNew": False, "ID": activity[0]["id"],"Tarball_URL": activity[0]["tarball_url"], "Zipball_URL": activity[0]["zipball_url"]}