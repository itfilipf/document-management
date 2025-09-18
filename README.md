# Propylon Document Manager Assessment

The Propylon Document Management Technical Assessment is a simple (and incomplete) web application consisting of a basic API backend and a React based client.  This API/client can be used as a bootstrap to implement the specific features requested in the assessment description. 

## Getting Started
### API Development
The API project is a [Django/DRF](https://www.django-rest-framework.org/) project that utilizes a [Makefile](https://www.gnu.org/software/make/manual/make.html) for a convenient interface to access development utilities. This application uses [SQLite](https://www.sqlite.org/index.html) as the default persistence database you are more than welcome to change this. This project requires Python 3.11 in order to create the virtual environment.  You will need to ensure that this version of Python is installed on your OS before building the virtual environment.  Running the below commmands should get the development environment running using the Django development server.
1. `$ make build` to create the virtual environment.
2. `$ make fixtures` to create a small number of fixture file versions.
3. `$ make serve` to start the development server on port 8001.
4. `$ make test` to run the limited test suite via PyTest.

### Testing the API with real db data
You can use the provided Postman collection file to help you to test the API with real data.
Before using the collection make sure that you have called management command `seed-data` to create some sample data.
1. `$ make seed-data` django management command to create sample data for Alise and Bob.
2. `$ make serve` to start the development server on port 8001.
3. Import the Postman collection file from tests directory `postman_collection_import.json` into your Postman application
4. Fill the collection variables and make requests

### Create specific user using management command
You can create a specific user using the provided management command `create-user-with-file`.

You have to forward **email**, **password** and a **url** where created file will be stored.
Example of crating a user:

`$ make create-user-with-file email="johndoe@exmaple.com" password="secretpw" url="secret_files/secret.txt`
# API Documentation

All endpoints require authentication with a token in the header.

## Authentication
**POST** `/auth-token/`  
Login with email + password.

**Request Example:**
```json
{
  "username": "alice@example.com",
  "password": "test1234"
}
```
**Response Example:**
```json
{
  "token": "your_auth_token"
}
```
**Possible HTTP Status Codes:**

- **HTTP 200 OK**

- **400 Bad Request** – Invalid username or password.


## List Documents
**GET** `/api/documents/`  

Retrieve a paginated list of documents owned by the authenticated user.  
Each document includes all available revisions.

**Query Parameters:**
- `page` *(optional, int)* – Page number (default: 1)
- `page_size` *(optional, int)* – Number of items per page (default: 10, max: 100)

**Response Example:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "url": "documents/reviews/review.pdf",
      "revisions": [
        {"file_name": "review.pdf", 
          "version_number": 0, 
          "content_hash": "abc123", 
          "shared_users": [{"id": 2, "email": "bob@example.com", "name": "Bob"}]
        },
        {"file_name": "review.pdf",
          "version_number": 1,
          "content_hash": "def456",
          "shared_users": []
        }
      ]
    },
    {
      "url": "documents/contracts/nda.docx",
      "revisions": [
        {"file_name": "nda.docx", "version_number": 0, "content_hash": "ghi789", "shared_users":  []}
      ]
    }
  ]
}
```
**Possible HTTP Status Codes:**

- **200 OK**– Documents successfully retrieved.

- **403 Forbidden** – Missing or invalid authentication token..

## Upload Document
**POST** `/api/documents/{url}/`  

Upload a new document or a new revision of an existing document.  
When uploading to the same `url`, the `version_number` is automatically incremented.  

**Parameters:**
- `file` *(required, multipart)* – The file to upload.

**Response Example:**
```json
{
  "id": 12,
  "url": "docs/new.txt",
  "user": "1",
  "version": 0,
  "content_hash": "9f2c...",
  "shared_users": [
  ]
}
```
**Possible HTTP Status Codes:**

- **201 Created** – Document uploaded successfully (new file or new revision).

- **400 Bad Request** – Missing file parameter or invalid request format.

- **403 Forbidden** – Missing or invalid authentication token.

## Download Document
**GET** `/api/documents/{url}/`  

Download the latest revision of a document or a specific revision by version number.  

**Query Parameters:**
- `revision` *(optional, int)* – Specific version number of the document.  
  - If omitted, the latest revision is returned.  

**Examples:**
- `GET /api/documents/docs/new.txt/` → returns the latest revision  
- `GET /api/documents/docs/new.txt/?revision=0` → returns the first revision  

**Response:**  
- Returns a file response with the correct filename and content.  

**Possible HTTP Status Codes:**
- **200 OK** – Document successfully retrieved.
- **400 Bad Request** – Invalid revision parameter or bad request.
- **403 Forbidden** – Missing or invalid authentication token.
- **404 Not Found** – Document or specific revision not found.


## Retrieve by Hash (CAS)
**GET** `/api/documents/hash/{content_hash}/`  

Retrieve a document directly by its unique content hash.  
This supports **Content Addressable Storage (CAS)**
A user can only access files they own, even if the hash is known.

**Path Parameters:**
- `content_hash` *(required, string)* – SHA-256 hash of the file content.

**Response:**  
- Returns a file response with the correct filename and content.

**Possible HTTP Status Codes:**
- **200 OK** – Document successfully retrieved by hash.
- **403 Forbidden** –  Missing or invalid authentication token.
- **404 Not Found** – No document with the given hash exists for the user or user can not see document.

## Share Document Access by emails
**POST** `/api/documents/hash/{content_hash}/share/`  

Allows the document owner to share access with other users by email.  
Only the owner of a document can update its sharing list.  

**Path Parameters:**
- `content_hash` *(required, string)* – SHA-256 hash of the document to share.

**Body Parameters (JSON):**
- `emails` *(required, array of strings)* – List of user emails to share the document with.  
  - If the email corresponds to an existing user and is not already shared  -a new share is created.  
  - If the email is already shared - nothing changes.  
  - If an email was previously shared but is not included in the new list - the share is removed.  
  - If an email does not correspond to a user in the system - it is returned in the `not_found` list.  

**Request Example:**
```json
{
  "emails": ["bob@example.com", "carol@example.com"]
}
```
**Response Example:**
```json
{
    "shared_with": ["bob@example.com",],
    "not_found": ["carol@example.com",],
    "removed": ["john@example.com",]
 }
 ```

## File Endpoints

### Client Development 
See the Readme [here](https://github.com/propylon/document-manager-assessment/blob/main/client/doc-manager/README.md)

##
[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
