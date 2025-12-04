// API Layer - Replaces FastAPI endpoints with JavaScript functions
const API = {
    // ==================== AUTHENTICATION ====================
    
    async login(code) {
        try {
            const users = await DB.getAll('users');
            const user = users.find(u => u.code === code);
            
            if (user) {
                // Store user session
                localStorage.setItem('currentUser', JSON.stringify(user));
                return { success: true, user };
            }
            return { success: false, message: 'Codice errato' };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, message: 'Errore durante il login' };
        }
    },

    getCurrentUser() {
        const userStr = localStorage.getItem('currentUser');
        return userStr ? JSON.parse(userStr) : null;
    },

    logout() {
        localStorage.removeItem('currentUser');
    },

    async getUsers() {
        return await DB.getAll('users');
    },

    // ==================== TIMBRATURE ====================
    
    async getTimbrature(userId, date) {
        try {
            const allTimbrature = await DB.getByIndex('timbrature', 'utente_data', [parseInt(userId), date]);
            return allTimbrature;
        } catch (error) {
            console.error('Get timbrature error:', error);
            return [];
        }
    },

    async saveTimbratura(data, sostituisci = false) {
        try {
            // Check if timbratura already exists for this user and date
            const existing = await DB.getByIndex('timbrature', 'utente_data', [data.id_utente, data.data]);
            
            if (existing.length > 0 && !sostituisci) {
                return { modifica: true, message: 'Timbratura già esistente' };
            }

            if (existing.length > 0 && sostituisci) {
                // Update existing
                const updated = { ...existing[0], ...data };
                await DB.update('timbrature', updated);
                return { success: true, message: 'Timbratura aggiornata' };
            }

            // Add new
            await DB.add('timbrature', data);
            return { success: true, message: 'Timbratura salvata' };
        } catch (error) {
            console.error('Save timbratura error:', error);
            throw error;
        }
    },

    async deleteTimbratura(id) {
        try {
            await DB.delete('timbrature', parseInt(id));
            return { success: true };
        } catch (error) {
            console.error('Delete timbratura error:', error);
            throw error;
        }
    },

    // ==================== LAVORI ====================
    
    async getLavori(date) {
        try {
            return await DB.getByIndex('lavori', 'data', date);
        } catch (error) {
            console.error('Get lavori error:', error);
            return [];
        }
    },

    async saveLavoro(data) {
        try {
            await DB.add('lavori', data);
            return { success: true };
        } catch (error) {
            console.error('Save lavoro error:', error);
            throw error;
        }
    },

    async deleteLavoro(id) {
        try {
            await DB.delete('lavori', parseInt(id));
            return { success: true };
        } catch (error) {
            console.error('Delete lavoro error:', error);
            throw error;
        }
    },

    // ==================== ESPORTAZIONE ====================
    
    async getAttivita(filters) {
        try {
            const { data_da, data_a, commessa } = filters;
            let lavori = await DB.getAll('lavori');

            // Filter by date range
            if (data_da) {
                lavori = lavori.filter(l => l.data >= data_da);
            }
            if (data_a) {
                lavori = lavori.filter(l => l.data <= data_a);
            }

            // Filter by commessa
            if (commessa) {
                lavori = lavori.filter(l => l.commessa === commessa);
            }

            // Calculate totals
            const totali = {
                contanti: 0,
                assegni: 0,
                bonifico: 0,
                finanziamento: 0,
                negozio: 0,
                saldato: 0,
                sospeso: 0
            };

            lavori.forEach(l => {
                switch (l.saldo) {
                    case 'Contanti':
                        totali.contanti += l.saldato || 0;
                        break;
                    case 'Assegno':
                        totali.assegni += l.saldato || 0;
                        break;
                    case 'Bonifico':
                        totali.bonifico += l.saldato || 0;
                        break;
                    case 'Finanziamento':
                        totali.finanziamento += l.saldato || 0;
                        break;
                    case 'Pag. Negozio':
                        totali.negozio += l.saldato || 0;
                        break;
                    case 'Sospeso':
                        totali.sospeso += l.saldato || 0;
                        break;
                }

                if (l.saldo !== 'Sospeso' && l.saldo !== 'Pag. Negozio') {
                    totali.saldato += l.saldato || 0;
                }
            });

            return { lavori, totali };
        } catch (error) {
            console.error('Get attivita error:', error);
            return { lavori: [], totali: {} };
        }
    },

    async esportaPDF(filters) {
        try {
            // Check if jsPDF is loaded
            if (typeof jspdf === 'undefined') {
                throw new Error('jsPDF library not loaded');
            }

            const { lavori, totali } = await this.getAttivita(filters);

            // Create PDF using jsPDF
            const { jsPDF } = jspdf;
            const doc = new jsPDF();

            // Title
            doc.setFontSize(18);
            doc.text('Report Attività', 105, 15, { align: 'center' });

            // Date range
            doc.setFontSize(10);
            if (filters.data_da && filters.data_a) {
                doc.text(`Periodo: ${filters.data_da} - ${filters.data_a}`, 105, 25, { align: 'center' });
            }

            // Table header
            let y = 35;
            doc.setFontSize(9);
            doc.setFont(undefined, 'bold');
            doc.text('Commessa', 10, y);
            doc.text('Data', 40, y);
            doc.text('Cliente', 65, y);
            doc.text('Contratto', 110, y);
            doc.text('Saldato', 145, y);
            doc.text('Extra', 175, y);

            // Table rows
            doc.setFont(undefined, 'normal');
            y += 7;

            lavori.forEach(l => {
                if (y > 270) {
                    doc.addPage();
                    y = 20;
                }

                doc.text(l.commessa || '', 10, y);
                doc.text(l.data || '', 40, y);
                doc.text((l.cliente || '').substring(0, 20), 65, y);
                doc.text(`€${(l.contratto || 0).toFixed(2)}`, 110, y);
                doc.text(`€${(l.saldato || 0).toFixed(2)}`, 145, y);
                doc.text(`€${(l.extra_consegna || 0).toFixed(2)}`, 175, y);

                y += 6;
            });

            // Totals
            y += 10;
            doc.setFont(undefined, 'bold');
            doc.text('Totali:', 10, y);
            doc.setFont(undefined, 'normal');
            y += 7;
            doc.text(`Contanti: €${totali.contanti.toFixed(2)}`, 10, y);
            y += 6;
            doc.text(`Assegni: €${totali.assegni.toFixed(2)}`, 10, y);
            y += 6;
            doc.text(`Bonifico: €${totali.bonifico.toFixed(2)}`, 10, y);
            y += 6;
            doc.text(`Finanziamento: €${totali.finanziamento.toFixed(2)}`, 10, y);
            y += 6;
            doc.text(`Totale Saldato: €${totali.saldato.toFixed(2)}`, 10, y);

            // Download PDF
            doc.save('attivita.pdf');

            return { success: true };
        } catch (error) {
            console.error('Export PDF error:', error);
            throw error;
        }
    }
};
