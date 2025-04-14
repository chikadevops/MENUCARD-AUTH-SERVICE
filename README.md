# MenuCard App

The MenuCard App project is a web-based platform for restaurant administrators to manage their digital menu, restaurant operations, and customer interactions.

## Cloning the Repository

- To clone the repository, run the following command:

  ```sh
    git clone https://github.com/hngprojects/Menucard-App-Team-D-Backend
  ```

- Navigate into the project directory

  ```sh
  cd Menucard-App-Team-D-Backend
  ```

## MenuCard App Project Architecture

```bash
Menucard-App-Team-D-Backend/
│-- src/               # Source code
│ ├── configs/         # App settings
│ ├── controllers/     # Request handlers
│ ├── middleware/      # Auth & validation
│ ├── models/          # Database schema
│ ├── routes/          # API endpoints
│ ├── services/        # Business logic
│ ├── utils/           # Helper functions
│ ├── app.js           # App entry point
│-- tests/             # Test cases
│-- .env.sample        # Env variables
│-- .gitignore         # Git exclusions
│-- package.json       # Project metadata
│-- README.md          # Project guide
│-- index.js           # Server entry
```

## Setup Instructions

- Ensure you have Node.js installed (recommended: latest LTS version).

## Install Dependencies

Run the following command to install dependencies:

```bash
npm ci
```

## Create a .env file from .env.sample

Copy `.env.sample` to `.env` and update the necessary values:

```bash
cp .env.sample .env
```

## To Run Project Locally

Start the development server:

```bash
npm run dev
```

## Running Tests with Jest

**a. Install Jest**

```bash
npm install --save-dev jest
```

**b. Run All Tests in the Project**

```bash
npm test
```

**c. Run Tests and Generate Coverage Report**

```bash
npm run coverage
```

## API Documentation

The API documentation is available via Swagger UI. After starting the server:

1. Access Swagger UI at: `http://localhost:8000/api-docs`
2. Browse and test available endpoints
3. View request/response schemas and examples


Alternatively, import the OpenAPI spec into Postman for testing.

## Contribution Guidelines

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request to learn about our development process, how to propose bugfixes and improvements, and how to build and test your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
