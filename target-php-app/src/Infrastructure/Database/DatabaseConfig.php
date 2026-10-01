<?php

declare(strict_types=1);

namespace OrderBillingSystem\Infrastructure\Database;

use InvalidArgumentException;

/**
 * Configuração Segura de Banco de Dados.
 * - Carrega credenciais exclusivamente de variáveis de ambiente.
 * - Implementa __debugInfo() para NUNCA exibir a senha em var_dump(), print_r() ou logs.
 */
final readonly class DatabaseConfig
{
    public string $driver;
    public string $host;
    public int $port;
    public string $database;
    public string $user;
    private string $password;

    public function __construct(
        ?string $host = null,
        ?string $database = null,
        ?string $user = null,
        ?string $password = null,
        int $port = 3306,
        string $driver = 'mysql'
    ) {
        $this->driver = $driver;
        $this->host = $host ?? (getenv('DB_HOST') ?: '127.0.0.1');
        $this->database = $database ?? (getenv('DB_NAME') ?: 'order_billing_db');
        $this->user = $user ?? (getenv('DB_USER') ?: 'db_order_user');
        $this->password = $password ?? (getenv('DB_PASSWORD') ?: '');
        $this->port = (int) ($port ?: (getenv('DB_PORT') ?: 3306));

        if (trim($this->host) === '' || trim($this->database) === '') {
            throw new InvalidArgumentException('Database host and database name cannot be empty.');
        }
    }

    public function getDsn(): string
    {
        if ($this->driver === 'sqlite') {
            return "sqlite:{$this->database}";
        }
        return "{$this->driver}:host={$this->host};port={$this->port};dbname={$this->database};charset=utf8mb4";
    }

    public function getUser(): string
    {
        return $this->user;
    }

    public function getPassword(): string
    {
        return $this->password;
    }

    /**
     * CAMADA DE SEGURANÇA: Mascaramento ativo de credenciais.
     * Retorna array seguro quando inspecionado em debug/logs.
     */
    public function __debugInfo(): array
    {
        return [
            'driver' => $this->driver,
            'host' => $this->host,
            'port' => $this->port,
            'database' => $this->database,
            'user' => $this->user,
            'password' => '******** (REDACTED)',
        ];
    }
}
