const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const productRoutes = require('./routes/products');
const orderRoutes = require('./routes/orders');
const paymentRoutes = require('./routes/payments');

const app = express();
app.use(cors());
app.use(express.json());

app.use('/products', productRoutes);
app.use('/orders', orderRoutes);
app.use('/payments', paymentRoutes);

mongoose.connect(process.env.MONGO_URL).then(() => {
  app.listen(process.env.PORT || 3000, () => console.log('shop running'));
});
