// 1. Importar Express e o cliente pg
const express = require('express');
const { Pool } = require('pg');
const app = express();
const port = 3000;

// 2. Configurar a conexão com o Neon
// Use a string de conexão completa do Neon.
// É melhor carregar isso de uma variável de ambiente (process.env.DATABASE_URL)
const connectionString = 'postgresql://neondb_owner:npg_Iflxy7RMmnH6@ep-delicate-resonance-ahxuy5yh-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require';

const pool = new Pool({
    connectionString: connectionString,
    // Opcional: Neon já exige SSL, mas é bom especificar
    ssl: {
        rejectUnauthorized: false
    }
});

// 3. Testar a Conexão
pool.query('SELECT NOW()', (err, res) => {
    if (err) {
        console.error('Erro ao conectar ao banco de dados Neon:', err);
    } else {
        console.log('Conexão com o Neon estabelecida com sucesso em:', res.rows[0].now);
    }
});

// Outras configurações (middlewares, rotas, etc.)

app.listen(port, () => {
    console.log(`Servidor rodando em http://localhost:${port}`);
});