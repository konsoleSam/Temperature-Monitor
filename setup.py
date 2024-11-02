from cx_Freeze import setup,Executable
from os import path

setup(name="Password Manager",
      options={
          "build_exe":{
              "excludes":[],
              "includes":["sqlalchemy.dialects.sqlite"],
              "packages":[],
              "include_files":["static","templates","license.txt"]
              }
          },
      version="V10.25.24",
      description="Password Manager",
      long_description="Password Manager",
      long_description_content_type="text/markdown",
      author="Samuel Willis",
      author_email="N/A",
      maintainer="Samuel Willis",
      maintainer_email="N/A",
      url="N/A",
      download_url="N/A",
      license="Password Manager © 2024 by Samuel Willis is licensed under CC BY-SA 4.0",
      license_files="N/A",
      keywords="N/A",
      project_urls="N/A",
      copyright="Password Manager © 2024 by Samuel Willis is licensed under CC BY-SA 4.0",
      executables=[
          Executable(
              script="app.py",
              base="Win32GUI",
              icon=path.join(path.dirname(__file__),"static","favicon.ico"),
              target_name="Password-Manager"
                     )
          ]
      )