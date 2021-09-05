from tuxemon.mod_manager import Manager

#man = Manager("http://127.0.0.1:5000")
man = Manager("http://tuxemon-content-server-dev.herokuapp.com:80")

man.update_all()
man.download_package("mainDP", 0)
