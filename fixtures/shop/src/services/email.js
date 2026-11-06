const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
});

async function sendReceipt(to, order) {
  await transporter.sendMail({ to, subject: 'Your order', text: `Order ${order._id}: ${order.amount}` });
}

module.exports = { sendReceipt };
