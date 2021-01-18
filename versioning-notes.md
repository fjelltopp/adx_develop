Versioning notes:

1.Browser blocks requests to giftless as cross domain web security
Quick workaround for chrome only (didn’t find any for firefox)

    google-chrome --disable-web-security --user-data-dir=~/tmp/chrome

Things to have a look at:
1. To modify datapub: Init git submodules of ckanext-blog-storage to use the React UI for resource upload

```
    ➜  ckanext-blob-storage git:(master) git submodule init
    ➜  ckanext-blob-storage git:(master) git submodule update
```

Plan forwards + TODOs:
- [ ] Nginx config for giftless service to resolve the cross domain security
- [ ] Solve giftless proper authentication instead of current `a+w`
- [ ] Modify React file upload UI to look good (UNAIDS themed)
Substitue just the "File upload snippet" in resource upload form
- [ ] Check out how to make resouce scheming to go with blob storage React UI
- [ ] Existing data migration to giftless
- [ ] Consider storage options to be used by giftless (is current filesystem production ready solution?)
- [ ] Investigate 2.9 Activity Stream working with ckanext-versioning
Even if it works only with named revisions it's still a big win for ADR
- [ ] Investigate the datapusher + versioning
- [x] Does ckanext-versioning create new revisions on each resource upload? Do we need the user to create a revision each time they upload file?
YEST IT DOES!
- [ ] fileuploader-ui does it work with ckanext-versioning?
