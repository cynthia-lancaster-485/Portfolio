# PonyExpress - a messaging application

## Frontend

The frontend of the application is written in javascript using

- [react](https://https://react.dev/)
- [tailwind](https://tailwindcss.com/)
- [vite](https://vite.dev/)

### Setup

- Ensure you have modern version of Node.js installed, at least version 20. (I am using
  Node version 23.8.0.)

- If you are using `npm` on the command line, you can install the dependencies from within
  the `frontend` folder by running

  ```bash
  npm install
  ```

- If you are using `npm` in your IDE, follow your IDE instructions for installing Node
  dependencies.

### Development

Start the frontend server from within the `frontend` folder by running

```bash
npm run dev
```

Once the server is running, you can visit the site at `http://localhost:5173`.

### Tailwind CSS

The project is set up to use TailwindCSS. The only styles applied initially are in
the `body` and `div#root` components in `index.html` and the headers in `App.jsx`.
You may change these styles as you see fit.

### Routing

The project is set up to use `react-router` to define routes. There are two routes already
provided in `App.jsx`.

### Queries

The project is set up to use `react-query` for managing queries, mutations, and query
data. The query client and query client provider are in use in `App.jsx`.
