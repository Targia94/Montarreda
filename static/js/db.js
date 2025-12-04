// Database wrapper for IndexedDB
const DB = {
    name: 'MontarredaDB',
    version: 1,
    db: null,

    // Initialize database
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.name, this.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                console.log('✅ Database initialized');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Users table
                if (!db.objectStoreNames.contains('users')) {
                    const usersStore = db.createObjectStore('users', { keyPath: 'id', autoIncrement: true });
                    usersStore.createIndex('code', 'code', { unique: true });
                    console.log('📦 Created users table');
                }

                // Timbrature table
                if (!db.objectStoreNames.contains('timbrature')) {
                    const timbratureStore = db.createObjectStore('timbrature', { keyPath: 'id', autoIncrement: true });
                    timbratureStore.createIndex('id_utente', 'id_utente', { unique: false });
                    timbratureStore.createIndex('data', 'data', { unique: false });
                    timbratureStore.createIndex('utente_data', ['id_utente', 'data'], { unique: false });
                    console.log('📦 Created timbrature table');
                }

                // Lavori table
                if (!db.objectStoreNames.contains('lavori')) {
                    const lavoriStore = db.createObjectStore('lavori', { keyPath: 'id', autoIncrement: true });
                    lavoriStore.createIndex('data', 'data', { unique: false });
                    lavoriStore.createIndex('commessa', 'commessa', { unique: false });
                    console.log('📦 Created lavori table');
                }
            };
        });
    },

    // Generic get all from store
    async getAll(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },

    // Generic get by ID
    async getById(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(id);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },

    // Generic add
    async add(storeName, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(data);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },

    // Generic update
    async update(storeName, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(data);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },

    // Generic delete
    async delete(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(id);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    },

    // Get by index
    async getByIndex(storeName, indexName, value) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readonly');
            const store = transaction.objectStore(storeName);
            const index = store.index(indexName);
            const request = index.getAll(value);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    },

    // Clear all data from a store
    async clear(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(storeName, 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    },

    // Populate with sample data
    async populateSampleData() {
        try {
            // Check if users already exist
            const users = await this.getAll('users');
            if (users.length > 0) {
                console.log('ℹ️ Sample data already exists');
                return;
            }

            // Add default user
            await this.add('users', {
                full_name: 'Giovanni',
                code: '0000'
            });

            console.log('✅ Sample data populated');
        } catch (error) {
            console.error('❌ Error populating sample data:', error);
        }
    }
};

// Initialize database on load
(async () => {
    try {
        await DB.init();
        await DB.populateSampleData();
    } catch (error) {
        console.error('❌ Database initialization failed:', error);
    }
})();
