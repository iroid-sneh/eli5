const jwt = require('jsonwebtoken');

function requireAuth(req, res, next) {
  const token = (req.headers.authorization || '').replace('Bearer ', '');
  try {
    req.user = jwt.verify(token, 'super-secret-jwt-key');
    next();
  } catch (e) {
    res.status(401).json({ error: 'login required' });
  }
}

module.exports = { requireAuth };
