EchoMind — Setup Log
Project Initialization

The development environment for EchoMind was prepared using Anaconda and Visual Studio Code. The goal of this stage was to establish a stable and reproducible development environment before beginning system implementation.

1. Python Environment Setup

An isolated Conda environment was created to prevent dependency conflicts with the global Python installation.

The global system Python version on the machine is:

Python 3.14

However, for compatibility with AI libraries and database drivers, a dedicated environment was created using Python 3.11.

Environment Creation

Command executed:

conda create -n echomind python=3.11
Environment Activation
conda activate echomind

After activation, verification was performed:

python --version

Output:

Python 3.11.14

This confirms the project will run on Python 3.11.14.

2. Project Workspace Creation

A new project directory was created to host the EchoMind codebase.

Commands executed:

mkdir echomind
cd echomind

This directory serves as the root workspace for the entire system.

3. VS Code Workspace Initialization

Visual Studio Code was launched from the activated Conda environment using:

code

Launching VS Code this way ensures the editor inherits the currently active environment.

The workspace was therefore automatically configured to use:

Python 3.11.14 (echomind)

This was verified via the VS Code status bar.

4. Python Interpreter Verification

The interpreter inside the VS Code terminal was verified using:

python --version

Output confirmed:

Python 3.11.14

This ensures that all commands executed inside the workspace will use the correct Conda environment.

5. Initial Project Structure

The base folder structure for EchoMind was created to reflect the architectural modules of the system.

Planned project structure:

echomind
│
├── app
│   ├── connectors
│   ├── preprocessing
│   ├── embeddings
│   ├── db
│   ├── scheduler
│   └── logging
│
├── models
├── pipelines
│
├── docs
│
├── requirements.txt
├── README.md
└── main.py

This modular layout separates concerns between:

ingestion connectors

preprocessing

embeddings

database logic

pipeline orchestration

6. Documentation Setup

A documentation directory was created to track development progress.

Directory created:

docs/

Inside this folder, a build log file was created:

docs/setup_log.md

This file serves as the engineering journal for the project.

All setup steps, architectural decisions, and implementation milestones will be recorded here.

7. Dependency Management Setup

A dependency declaration file was created to ensure reproducible builds.

File created:

requirements.txt

Initial dependencies added:

python-dotenv
psycopg2-binary
sqlalchemy
pgvector

Dependencies were installed using:

pip install -r requirements.txt

After installation, exact package versions were recorded using:

pip freeze > requirements.txt

This ensures consistent environments across different machines.

8. Project README Creation

A root project description file was created:

README.md

This document contains:

project overview

tech stack

environment setup instructions

The README serves as the entry point for developers interacting with the repository.

Current Status

At this stage the following components are ready:

• Python environment configured
• Conda environment active
• VS Code workspace configured
• Project directory created
• Documentation system initialized
• Dependency management configured

The development environment is now fully prepared for implementing the backend components of EchoMind.

The next stage will focus on installing and configuring the PostgreSQL + pgvector database, which will serve as the system's long-term memory storage.

# 9. PostgreSQL Installation

The PostgreSQL database server was installed to provide persistent storage for EchoMind's memory system.

The EnterpriseDB installer was used to install PostgreSQL along with pgAdmin and command-line tools.

Installed components:
- PostgreSQL Server
- pgAdmin 4
- PostgreSQL Command Line Tools

Configuration settings used during installation:

Port:
5432

Database superuser:
postgres

A development password was configured for the postgres user.

After installation, the PostgreSQL command-line tool was verified using:

psql --version

This confirmed that PostgreSQL was successfully installed and available on the system.

PostgreSQL will be used as the primary persistence layer for EchoMind, with the pgvector extension enabling vector embeddings for semantic memory retrieval.


# 10. PostgreSQL Configuration and Database Creation

After installing PostgreSQL 16.13, the PostgreSQL command line tools were added to the system PATH.

Path added to system variables:

C:\Program Files\PostgreSQL\16\bin

This enabled the `psql` command to be executed globally from the terminal.

Verification command executed:

psql --version

Output confirmed installation:

psql (PostgreSQL) 16.13

Next, a connection was established to the PostgreSQL server using the default superuser.

Command used:

psql -U postgres

After authentication, the PostgreSQL interactive shell was accessed.

Existing databases were inspected using:

\l

To isolate the project data, a dedicated database for EchoMind was created:

CREATE DATABASE echomind;

After creation, the session switched to the new database using:

\c echomind

The active database connection was verified using:

SELECT current_database();

Output confirmed the active database as:

echomind

This database will store the EchoMind persistence layer including memory chunks, entities, events, and vector embeddings.

# 21. Successful Compilation and Installation of pgvector

The pgvector extension was compiled from source using Microsoft Visual Studio C++ build tools.

The compilation was performed using the following commands inside the x64 Native Tools Command Prompt:

set "PGROOT=C:\Program Files\PostgreSQL\16"
cd %TEMP%
git clone --branch v0.8.2 https://github.com/pgvector/pgvector.git
cd pgvector
nmake /F Makefile.win
nmake /F Makefile.win install

Explanation:

PGROOT → specifies the PostgreSQL installation directory  
git clone → downloads the pgvector source code  
nmake → compiles the extension using Microsoft build tools  
nmake install → copies compiled files into PostgreSQL directories

---

## Build Output

The compilation generated the shared library:

vector.dll

This file implements the vector data type and indexing algorithms.

The library was installed into:

C:\Program Files\PostgreSQL\16\lib

Extension metadata and SQL scripts were installed into:

C:\Program Files\PostgreSQL\16\share\extension

Installed files include:

vector.control
vector--0.8.2.sql
vector--0.8.1--0.8.2.sql
(other upgrade scripts)

---

## Enabling the Extension

The extension was enabled inside the EchoMind database using:

CREATE EXTENSION vector;

Verification query:

SELECT '[1,2,3]'::vector;

Successful execution confirmed that the vector data type is available in PostgreSQL.

This enables PostgreSQL to store and search embedding vectors required for EchoMind's semantic memory system.