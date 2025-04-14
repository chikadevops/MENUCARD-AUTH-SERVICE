//Dependencies
const express = require('express');
const morgan = require('morgan');
const helmet = require('helmet');
const cors = require('cors');
const limiter = require('./middlewares/rateLimiter.middleware');

// imported files
const adminRouter = require('./routes/auth.route');
const { swaggerUi, specs} = require('../swagger');
const logger = require('./utils/logger');

const app = express();

//security middlewares
app.use(cors());
app.use(helmet());
app.use(limiter);

app.use(morgan('dev'));
app.use(express.json());

app.use(morgan('dev'));

app.get('/', (req, res) => {
  logger.info(`Start: Welcome`);
  res.status(200).send('Welcome to Project Menucard');
});

app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(specs));

app.use('/api/v1/admin/', adminRouter);

app.use('**', (req, res) => {
  res.status(404).send({ message: 'This route does not exist' });
});

module.exports = { app };
