qm clone 9200 401 --name k3s-a --format raw --full --storage vmdata
qm resize 401 scsi0 50G
qm set 401 --boot c --bootdisk scsi0
qm set 401 -cdrom /zfspool/filestore/vmdata/template/iso/k3s-seed-k3s-a.iso
