const express = require('express');
const Stripe = require('stripe');
const Order = require('../models/Order');
const { requireAuth } = require('../middleware/auth');

const stripe = new Stripe('sk_test_DEMO1234FAKE');
const router = express.Router();

router.post('/checkout', requireAuth, async (req, res) => {
  const intent = await stripe.paymentIntents.create({
    amount: req.body.amount,
    currency: 'usd',
    metadata: { orderId: req.body.orderId },
  });
  res.json({ clientSecret: intent.client_secret });
});

// Stripe calls this webhook when a payment finishes
router.post('/webhook', async (req, res) => {
  const event = req.body;
  if (event.type === 'payment_intent.succeeded') {
    await Order.findByIdAndUpdate(event.data.object.metadata.orderId, { status: 'paid' });
  }
  res.json({ received: true });
});

router.post('/refund', requireAuth, refundOrder);

async function refundOrder(req, res) {
  // TODO: implement refunds
}

module.exports = router;
