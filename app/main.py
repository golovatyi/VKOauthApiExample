import vk


class Main():



    def access_via_token(self,token):
        '''
        retrieves friendlist
        :param token: token
        :return: json-like data as dict
        '''
        self.oauth = vk.Session(access_token=token)
        self.api = vk.API(session=self.oauth)
        self.info = self.api.friends.get(order='random', v='5.8', fields=['photo_id'])
        return self.info

    def get_photo_uri(self, photo_id):
        '''
        #returns list [url]
        :param dict()
        :return: uris
        '''
        uris = []
        print('photoIDS: ')
        print(photo_id)
        #id: id, sizes:{bullshit}
        photos = self.api.photos.getById(photos=str(photo_id), photosizes=1, v='5.8')
        for item in photos:
            #перебор юзеров
            uris.append(item['photo_75'])

        return uris



if __name__ == "__main__":
    Main().main()
