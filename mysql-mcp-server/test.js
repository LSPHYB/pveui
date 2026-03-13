import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config();

async function testConnection() {
  const config = {
    host: process.env.MYSQL_HOST,
    port: parseInt(process.env.MYSQL_PORT || '3306'),
    user: process.env.MYSQL_USER,
    password: process.env.MYSQL_PASSWORD,
    database: process.env.MYSQL_DATABASE,
  };

  console.log('=== MySQL 连接测试 ===\n');
  console.log('配置信息:');
  console.log('Host:', config.host);
  console.log('Port:', config.port);
  console.log('User:', config.user);
  console.log('Database:', config.database);
  console.log('Password:', config.password ? '***' : '(空)');
  console.log('');

  // 测试 1: 不指定数据库
  console.log('测试 1: 连接到服务器 (不指定数据库)...');
  try {
    const conn1 = await mysql.createConnection({
      host: config.host,
      port: config.port,
      user: config.user,
      password: config.password,
      connectTimeout: 10000,
    });
    console.log('✅ 成功连接到 MySQL 服务器!');

    const [result] = await conn1.query('SELECT VERSION() as version, NOW() as time');
    console.log('   版本:', result[0].version);
    console.log('   时间:', result[0].time);

    await conn1.end();
  } catch (error) {
    console.error('❌ 连接失败:', error.message);
    console.error('   错误代码:', error.code);

    if (error.code === 'PROTOCOL_CONNECTION_LOST') {
      console.error('\n   可能原因:');
      console.error('   1. 安全组未放行您的 IP');
      console.error('   2. MySQL 防火墙阻止');
      console.error('   3. 用户不允许从您的 IP 连接');
    } else if (error.code === 'ER_ACCESS_DENIED_ERROR') {
      console.error('\n   用户名或密码错误!');
    } else if (error.code === 'ENOTFOUND') {
      console.error('\n   无法解析主机名,检查 MYSQL_HOST');
    } else if (error.code === 'ETIMEDOUT' || error.code === 'ECONNREFUSED') {
      console.error('\n   连接超时或被拒绝,检查:');
      console.error('   1. 主机地址是否正确');
      console.error('   2. 端口是否正确');
      console.error('   3. 安全组是否开放');
    }
    return;
  }

  // 测试 2: 连接到指定数据库
  console.log('\n测试 2: 连接到数据库 "' + config.database + '"...');
  try {
    const conn2 = await mysql.createConnection(config);
    console.log('✅ 成功连接到数据库!');

    const [tables] = await conn2.query('SHOW TABLES');
    console.log('   表数量:', tables.length);
    if (tables.length > 0) {
      console.log('   表列表:', tables.slice(0, 5).map(t => Object.values(t)[0]).join(', '));
    }

    await conn2.end();
  } catch (error) {
    console.error('❌ 连接数据库失败:', error.message);
    console.error('   错误代码:', error.code);
  }

  console.log('\n=== 测试完成 ===');
}

testConnection();