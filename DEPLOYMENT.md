# Deployment and updates

The user-provided repository is https://github.com/ahua-0503/OasisInsight-AICOMP. It was empty when checked. The local origin is already configured. After the initial commit, push from this directory:

```powershell
git push -u origin main
```

Complete GitHub authentication yourself; no credentials belong in files or chat.

In Streamlit Community Cloud, connect your GitHub account and choose:

- Repository: ahua-0503/OasisInsight-AICOMP
- Branch: main
- Main file path: app.py
- Advanced settings / Python: 3.12
- Secrets: none
- Preferred subdomain: oasisinsight; alternatives oasisinsight-aicomp or oasisinsight-xju (availability not checked)

After deployment, test the actual URL while signed out, on desktop and phone: four tabs, layer and trajectory switching, four feature responses, evidence images, About, governance CSV download, and refresh. Record first-load time. Local tests are not Linux/cloud tests.

For future updates, regenerate this deployment directory from the local source, review `git diff`, commit and push to main. Do not upload the parent research directory. Cloud tracks GitHub changes; ordinary app updates do not require a new application.

Official instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

