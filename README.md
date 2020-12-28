Deliberate self-harm (DSH) annotator
====================================

This is a Python application that annotates mentions of deliberate self-harm (DSH) in clinical texts. The algorithm determines whether a mention is negated or not, whether it is current or historical and whether it is relevant or not (e.g. is a hypothetical or asserted mention), as defined by the parameters of the associated study. The type of self-harm is also annotated in a normalised form.

This code exposes an ELG-compliant endpoint and infrastructure for packaging the application into a Docker container.

This folder contains the actual Python code and the `Dockerfile` to build the image, the `pipeline` folder contains the `docker-app.yml` and metadata necessary to register the app with the NHS-TA platform.  To build the zip file for NHS-TA, zip up the _contents_ of the pipeline folder (not the folder itself, `docker-app.yml` must be at the top level of the final zip file with no intervening directories):

```
cd pipeline
zip -r ../dsh_annotator.zip *
```
