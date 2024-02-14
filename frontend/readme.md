# React Parcel Manual WebApp

How to compiled from
* https://tailwindcss.com/docs/guides/parcel
* https://parceljs.org/getting-started/webapp/

```sh
npm init -y
npm install -D parcel
mkdir src
```

Update `package.json`
```json
  ...
  "scripts": {
    "start": "parcel",
    "build": "parcel build"
  },
```

```sh
npm install -D tailwindcss postcss
npx tailwindcss init
```

create `.postcssrc`
```
{
  "plugins": {
    "tailwindcss": {}
  }
}
```

Update `tailwind.config.js`

```
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Create `src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Create `src/index.html`

```html
<!doctype html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="./index.css" rel="stylesheet">
</head>
<body>
  <h1 class="text-3xl font-bold underline">
    Hello world!
  </h1>
</body>
</html>
```

```
npm install tailwindcss-animate class-variance-authority clsx tailwind-merge
```

Start development
```
npm start
```