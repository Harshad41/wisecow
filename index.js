const express = require('express');
const cowsay = require('cowsay');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  const cowText = cowsay.say({
    text: "Hello from WiseCow! 🐮",
    e: "oO",
    T: "U "
  });
  
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
        <title>WiseCow App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f8ff; }
            pre { background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐮 Welcome to WiseCow! 🐮</h1>
            <pre>${cowText}</pre>
            <p>Server is running on port ${PORT}</p>
        </div>
    </body>
    </html>
  `);
});

app.get('/health', (req, res) => {
  res.json({ status: 'OK', message: 'WiseCow is running!' });
});

app.listen(PORT, () => {
  console.log(`WiseCow app listening on port ${PORT}`);
  console.log(cowsay.say({
    text: `WiseCow server started on port ${PORT}!`,
    e: "oO",
    T: "U "
  }));
});