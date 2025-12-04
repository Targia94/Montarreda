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

            if (lavori.length === 0) {
                alert('Nessuna attività trovata per il periodo selezionato');
                return { success: false };
            }

            // Calcoli come in Python
            const totale_contratto = lavori.reduce((sum, l) => sum + (l.contratto || 0), 0);
            const totale_saldato = lavori.reduce((sum, l) => sum + (l.saldato || 0), 0);
            const extra_su_consegne = lavori.reduce((sum, l) => sum + (l.extra_consegna || 0), 0);
            const percentuale_trasporto = totale_contratto * 0.06;
            const totale_lordo = percentuale_trasporto + extra_su_consegne;

            const totale_contanti = totali.contanti;
            const totale_assegni = totali.assegni;
            const totale_bonifico = totali.bonifico;
            const totale_finanziamento = totali.finanziamento || 0;
            const totale_negozio = totali.negozio;
            const totale_sospeso = totali.sospeso;

            // Create PDF using jsPDF
            const { jsPDF } = jspdf;
            const doc = new jsPDF();

            // Title - esattamente come Python
            doc.setFontSize(16);
            doc.setFont('helvetica', 'bold');
            doc.text(`Attivita | ${filters.data_da || ''} - ${filters.data_a || ''}`, 105, 15, { align: 'center' });

            doc.setLineWidth(0.1);

            // Spaziatura prima della tabella
            let y = 35;
            doc.setFontSize(10);
            doc.setFont('helvetica', 'bold');
            
            // Header row - larghezze esatte come Python
            doc.cell(10, y - 5, 20, 10, 'Commessa', undefined, 'left');
            doc.cell(30, y - 5, 25, 10, 'Data', undefined, 'left');
            doc.cell(55, y - 5, 40, 10, 'Cliente', undefined, 'left');
            doc.cell(95, y - 5, 25, 10, 'Pagamento', undefined, 'left');
            doc.cell(120, y - 5, 25, 10, 'Contratto', undefined, 'left');
            doc.cell(145, y - 5, 25, 10, 'Saldo', undefined, 'left');
            doc.cell(170, y - 5, 20, 10, 'Extra', undefined, 'left');

            // Table rows
            doc.setFont('helvetica', 'normal');
            y += 10;

            lavori.forEach(l => {
                if (y > 270) {
                    doc.addPage();
                    y = 20;
                }

                // Dati con simbolo € come in Python
                doc.cell(10, y - 5, 20, 10, (l.commessa || '').substring(0, 8), undefined, 'left');
                doc.cell(30, y - 5, 25, 10, (l.data || '').substring(0, 10), undefined, 'left');
                doc.cell(55, y - 5, 40, 10, (l.cliente || '').substring(0, 15), undefined, 'left');
                doc.cell(95, y - 5, 25, 10, (l.saldo || '').substring(0, 12), undefined, 'left');
                doc.cell(120, y - 5, 25, 10, `${(l.contratto || 0).toFixed(2)} €`, undefined, 'left');
                doc.cell(145, y - 5, 25, 10, `${(l.saldato || 0).toFixed(2)} €`, undefined, 'left');
                doc.cell(170, y - 5, 20, 10, `${(l.extra_consegna || 0).toFixed(2)} €`, undefined, 'left');

                y += 10;
            });

            // Totals row - esattamente come Python
            doc.setFont('helvetica', 'bold');
            doc.cell(10, y - 5, 110, 10, 'Totale', undefined, 'right');
            doc.cell(120, y - 5, 25, 10, `${totale_contratto.toFixed(2)} €`, undefined, 'left');
            doc.cell(145, y - 5, 25, 10, `${totale_saldato.toFixed(2)} €`, undefined, 'left');
            doc.cell(170, y - 5, 20, 10, `${extra_su_consegne.toFixed(2)} €`, undefined, 'left');

            // Riepilogo Totali
            y += 20;
            doc.setFontSize(12);
            doc.setFont('helvetica', 'bold');
            doc.text('Riepilogo Totali', 10, y);
            
            y += 10;
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');

            // Totali table
            doc.cell(10, y - 5, 80, 10, 'Totale Contratto:', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${totale_contratto.toFixed(2)} €`, undefined, 'left');
            y += 10;

            doc.cell(10, y - 5, 80, 10, 'Percentuale trasporto (6%):', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${percentuale_trasporto.toFixed(2)} €`, undefined, 'left');
            y += 10;

            doc.cell(10, y - 5, 80, 10, 'Extra su consegne:', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${extra_su_consegne.toFixed(2)} €`, undefined, 'left');
            y += 10;

            doc.setFont('helvetica', 'bold');
            doc.cell(10, y - 5, 80, 10, 'Totale Lordo:', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${totale_lordo.toFixed(2)} €`, undefined, 'left');

            // Dettaglio Saldi
            y += 15;
            doc.setFontSize(12);
            doc.text('Dettaglio Saldi', 10, y);
            
            y += 10;
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');

            doc.cell(10, y - 5, 80, 10, 'Totale Contanti:', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${totale_contanti.toFixed(2)} €`, undefined, 'left');
            y += 10;

            doc.cell(10, y - 5, 80, 10, 'Totale Assegni:', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${totale_assegni.toFixed(2)} €`, undefined, 'left');
            y += 10;

            doc.cell(10, y - 5, 80, 10, 'Totale Bonifico:', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${totale_bonifico.toFixed(2)} €`, undefined, 'left');
            y += 10;

            doc.cell(10, y - 5, 80, 10, 'Totale Negozio:', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${totale_negozio.toFixed(2)} €`, undefined, 'left');
            y += 10;

            doc.setFont('helvetica', 'bold');
            doc.cell(10, y - 5, 80, 10, 'Totale:', undefined, 'left');
            const totale_pagamenti = totale_contanti + totale_assegni + totale_bonifico + totale_negozio;
            doc.cell(90, y - 5, 40, 10, `${totale_pagamenti.toFixed(2)} €`, undefined, 'left');
            y += 10;

            doc.setFont('helvetica', 'normal');
            doc.cell(10, y - 5, 80, 10, 'Totale Sospeso:', undefined, 'left');
            doc.cell(90, y - 5, 40, 10, `${totale_sospeso.toFixed(2)} €`, undefined, 'left');

            // Download PDF
            doc.save('attivita.pdf');

            return { success: true };
        } catch (error) {
            console.error('Export PDF error:', error);
            throw error;
        }
    },

    // ==================== BACKUP/RESTORE ====================
    
    async exportData() {
        try {
            const users = await DB.getAll('users');
            const lavori = await DB.getAll('lavori');

            const backup = {
                version: '1.0',
                timestamp: new Date().toISOString(),
                data: {
                    users,
                    lavori
                }
            };

            // Create JSON file and download
            const dataStr = JSON.stringify(backup, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `montarreda-backup-${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            URL.revokeObjectURL(url);

            return { success: true, message: 'Backup creato con successo!' };
        } catch (error) {
            console.error('Export data error:', error);
            throw error;
        }
    },

    async importData(file) {
        try {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                
                reader.onload = async (e) => {
                    try {
                        const backup = JSON.parse(e.target.result);
                        
                        // Validate backup structure
                        if (!backup.data || !backup.data.users || !backup.data.lavori) {
                            throw new Error('File di backup non valido');
                        }

                        // Confirm before overwriting
                        if (!confirm('⚠️ Questo sovrascriverà tutti i dati esistenti. Continuare?')) {
                            resolve({ success: false, message: 'Importazione annullata' });
                            return;
                        }

                        // Clear existing data
                        await DB.clear('users');
                        await DB.clear('lavori');

                        // Import users
                        for (const user of backup.data.users) {
                            await DB.add('users', user);
                        }

                        // Import lavori
                        for (const lavoro of backup.data.lavori) {
                            await DB.add('lavori', lavoro);
                        }

                        resolve({ 
                            success: true, 
                            message: `Importati ${backup.data.users.length} utenti e ${backup.data.lavori.length} lavori!` 
                        });
                    } catch (error) {
                        reject(error);
                    }
                };

                reader.onerror = () => reject(new Error('Errore nella lettura del file'));
                reader.readAsText(file);
            });
        } catch (error) {
            console.error('Import data error:', error);
            throw error;
        }
    }
};
