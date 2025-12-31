import React from 'react';
import { CURRENT_USER } from '../constants';
import { useAppStore } from '../store';
import { User, Bell, Shield, CreditCard, LogOut } from 'lucide-react';

const Settings: React.FC = () => {
    const { theme } = useAppStore();
  return (
    <div className="h-full overflow-y-auto p-6 md:p-10 custom-scrollbar">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-8">Settings</h1>

        <div className="max-w-3xl space-y-8">
            {/* Profile Section */}
            <section className="bg-white dark:bg-[#18181B] rounded-xl border border-zinc-200 dark:border-zinc-800 overflow-hidden">
                <div className="p-6 border-b border-zinc-100 dark:border-zinc-800">
                    <h2 className="text-lg font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
                        <User size={20} /> Profile
                    </h2>
                </div>
                <div className="p-6 space-y-6">
                    <div className="flex items-center gap-6">
                        <img src={CURRENT_USER.avatar} alt="Avatar" className="w-20 h-20 rounded-full" />
                        <div>
                            <button className="px-4 py-2 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700">
                                Change Avatar
                            </button>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Full Name</label>
                            <input type="text" defaultValue={CURRENT_USER.name} className="w-full px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none text-zinc-900 dark:text-white" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">Email</label>
                            <input type="email" defaultValue={CURRENT_USER.email} className="w-full px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none text-zinc-900 dark:text-white" />
                        </div>
                    </div>
                </div>
            </section>

             {/* Notifications */}
             <section className="bg-white dark:bg-[#18181B] rounded-xl border border-zinc-200 dark:border-zinc-800 overflow-hidden">
                <div className="p-6 border-b border-zinc-100 dark:border-zinc-800">
                    <h2 className="text-lg font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
                        <Bell size={20} /> Notifications
                    </h2>
                </div>
                <div className="p-6 space-y-4">
                     <label className="flex items-center justify-between">
                         <div>
                             <p className="font-medium text-zinc-900 dark:text-white">Email Digest</p>
                             <p className="text-sm text-zinc-500">Receive a daily summary of new matches</p>
                         </div>
                         <input type="checkbox" className="toggle" defaultChecked />
                     </label>
                     <label className="flex items-center justify-between">
                         <div>
                             <p className="font-medium text-zinc-900 dark:text-white">Application Updates</p>
                             <p className="text-sm text-zinc-500">Get notified when status changes</p>
                         </div>
                         <input type="checkbox" className="toggle" defaultChecked />
                     </label>
                </div>
            </section>
             
             {/* Danger Zone */}
             <div className="flex justify-end pt-4">
                 <button className="text-red-600 hover:text-red-700 font-medium text-sm flex items-center gap-2">
                     <LogOut size={16} /> Sign Out
                 </button>
             </div>
        </div>
    </div>
  );
};

export default Settings;
