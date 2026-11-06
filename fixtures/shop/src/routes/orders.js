const express = require('express');
const Order = require('../models/Order');
const Product = require('../models/Product');
const { requireAuth } = require('../middleware/auth');
const { sendReceipt } = require('../services/email');
const router = express.Router();

router.post('/', requireAuth, async (req, res) => {
  const order = await Order.create({ userId: req.user.id, items: req.body.items, amount: req.body.amount });
  for (const item of order.items) {
    const product = await Product.findById(item.productId);
    product.stock -= item.qty;
    await product.save();
  }
  sendReceipt(req.user.email, order).catch(() => {});
  res.json(order);
});

router.get('/mine', requireAuth, async (req, res) => {
  res.json(await Order.find({ userId: req.user.id }));
});

module.exports = router;
