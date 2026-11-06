const mongoose = require('mongoose');

const orderSchema = new mongoose.Schema({
  userId: String,
  items: [{ productId: String, qty: Number }],
  amount: Number,
  status: { type: String, default: 'pending' },
});

module.exports = mongoose.model('Order', orderSchema);
