# Software ACS project: Stenosis Annotations.
# Core Function for the LabelACS, the annotated bbx can be editable to resize and position changing.
# Developer: MA, Kochi University of Technology. 256013s@gs.kochi-tech.ac.jp
# Python, PyQt, Opencv.
# Core Function for Annotations.
# Beta version 0.1.

import os
import uuid
import sys
import cv2
import json
from PySide6.QtCore import Qt, Slot, QRectF, QRect, QPoint, QObject, Signal, QPointF
from PySide6.QtWidgets import (QMainWindow, QDialog, QLabel, 
                               QWidget, QPushButton, QVBoxLayout, 
                               QFileDialog, QMessageBox, QGraphicsView, 
                               QGraphicsScene, QToolBar, QApplication,
                               QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, QRubberBand,
                               QGraphicsPixmapItem, QMenu, QTextEdit, QGraphicsEllipseItem)
from PySide6.QtGui import (QPixmap, QIcon, QAction, QPainter, QPen, QMouseEvent, 
                           QBrush, QPainterPath, QColor, QImage)

class label_main(QMainWindow):
    def __init__(self, resize_info, save_root):
        super().__init__()
        self.setWindowTitle("ACS annotation, 簡単に使える")
        self.setWindowIcon(QIcon('./logo/label_acs.jpg'))

        self.resize_info = resize_info
        self.save_root = save_root
        self.init = 0
        self.current = 0
        self.end = 0

        self.test_UI()

    def test_UI(self):
        self.anno_scene = QGraphicsScene(self)
        pixmap = QPixmap("./logo/label_acs.jpg")
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.anno_scene.addItem(self.image_item)

        # To set the view size for image
        self.view = AnnotedView(self.anno_scene, self.image_item, False)
        self.view.fitInView(self.image_item, Qt.KeepAspectRatio)
        
        # img_area = self.image_item.boundingRect()
        # img_width = img_area.width()
        # img_height = img_area.height()
        # self.view.resize(img_width, img_height)

        select_button = QPushButton('動画データのファルダを選んでください')
        select_button.clicked.connect(self.vid_root)

        self.process_anno = QPushButton()
        
        previous_button = QPushButton('⬅ 前に イメージ')
        previous_button.clicked.connect(self.prev_img)

        save_button = QPushButton('動画のアノテーションは 確認してから それぞれに 保存してください')
        save_button.clicked.connect(self.save_anno)

        next_button = QPushButton('次に イメージ ➡')
        next_button.clicked.connect(self.next_img)

        exit_button = QPushButton('退出')
        exit_button.clicked.connect(self.close_window)
        
        layout = QVBoxLayout()
        layout.addWidget(self.process_anno)
        layout.addWidget(self.view)
        layout.addWidget(select_button)
        layout.addWidget(previous_button)
        layout.addWidget(save_button)
        layout.addWidget(next_button)
        layout.addWidget(exit_button)

        sreen_show = QWidget()
        sreen_show.setLayout(layout)
        self.setCentralWidget(sreen_show)

    @Slot()
    def vid_root(self):
        dir_dialog = QFileDialog.getExistingDirectory(self, "select a directory")
        if dir_dialog:
            print("directory of selected video for the annotations:", dir_dialog)
        self.selected_vid_pth = dir_dialog
        self.imgList_vid = os.listdir(self.selected_vid_pth)
        self.nums_imgs = len(self.imgList_vid)
        self.end = self.nums_imgs-1
        self.init_img = os.path.join(self.selected_vid_pth, self.imgList_vid[0])
        self.init_img = self.init_img.replace('\\', '/')

        pixmap = QPixmap(self.init_img)
        self.image_item.setPixmap(pixmap)

        self.anno_scene.setSceneRect(self.image_item.boundingRect())
        self.view.fitInView(self.image_item, Qt.KeepAspectRatio)
        
        img_name = self.init_img.split('/')[-1]
        patient_ID = img_name.split('_')[0]
        video_ID = img_name.split('-')[0]
        init_annIfo = os.path.join(self.save_root, patient_ID, video_ID, img_name.split('.')[0]+'.txt')
        if os.path.isfile(init_annIfo):
            self.display_anned(init_annIfo, self.image_item)

        self.view.annoing_label = True
        self.process_anno.setText('枚/合計：{}/{}, イメージ：{}'.format(self.current, self.nums_imgs, img_name))

    @Slot()
    def prev_img(self):
        self.view.annBBxes.clear()
        self.view.delBBxes.clear()
        if self.current == self.init:
            QMessageBox.information(QDialog(), '注意', f'最初の画像:{self.imgList_vid[self.current]}')
        else:
            self.current -= 1
        self.init_img = os.path.join(self.selected_vid_pth, self.imgList_vid[self.current])
        self.init_img = self.init_img.replace('\\', '/')

        pixmap = QPixmap(self.init_img)
        self.image_item.setPixmap(pixmap)

        for item in self.anno_scene.items():            # clear the annotated bbxes in previous image
            if isinstance(item, QGraphicsRectItem):
                self.anno_scene.removeItem(item)
        
        img_name = self.init_img.split('/')[-1]
        patient_ID = img_name.split('_')[0]
        video_ID = img_name.split('-')[0]
        init_annIfo = os.path.join(self.save_root, patient_ID, video_ID, img_name.split('.')[0]+'.txt')
        if os.path.isfile(init_annIfo):
            self.display_anned(init_annIfo, self.image_item)

        self.process_anno.setText('枚/合計：{}/{}, イメージ：{}'.format(self.current, self.nums_imgs, img_name))

    @Slot()
    def next_img(self):
        self.view.annBBxes.clear()
        self.view.delBBxes.clear()
        if self.current == self.end:
            QMessageBox.information(QDialog(), '注意', f'最後の画像:{self.imgList_vid[self.current]}')
        else:
            self.current += 1
        self.init_img = os.path.join(self.selected_vid_pth, self.imgList_vid[self.current])
        self.init_img = self.init_img.replace('\\', '/')
        
        for item in self.anno_scene.items():            # clear the annotated bbxes in previous image
            if isinstance(item, QGraphicsRectItem):
                self.anno_scene.removeItem(item)
        
        pixmap = QPixmap(self.init_img)
        self.image_item.setPixmap(pixmap)

        img_name = self.init_img.split('/')[-1]
        patient_ID = img_name.split('_')[0]
        video_ID = img_name.split('-')[0]
        init_annIfo = os.path.join(self.save_root, patient_ID, video_ID, img_name.split('.')[0]+'.txt')
        if os.path.isfile(init_annIfo):
            self.display_anned(init_annIfo, self.image_item)
        self.process_anno.setText('枚/合計：{}/{}, イメージ：{}'.format(self.current, self.nums_imgs, img_name))

    def display_anned(self, init_annIfo, image_item):
        with open(init_annIfo, 'r', encoding='utf-8') as txt_file:
            infos = txt_file.readlines()
        for bbx_dict in infos:
            bbx_dict = eval(bbx_dict.strip())                      # re-back to python dict type, 2025.12.06
            annoed_bbx = QRectF(float(bbx_dict['TopLx']), float(bbx_dict['TopLy']), 
                                float(bbx_dict['BottomRx']-bbx_dict['TopLx']),
                                float(bbx_dict['BottomRy']-bbx_dict['TopLy']))
            self.anno_scene.image_item = image_item
            self.anno_scene.img_rect = image_item.boundingRect()
            selected_bbx = annoed_bbx.intersected(self.anno_scene.img_rect)
            bbx_item = Editable2bbx(selected_bbx, self.anno_scene.img_rect)
            if bbx_dict['label'].split('_')[0] == 'mild':
                transparentC = QColor(0, 0, 255, 28)
                brushC = QBrush(transparentC)
                bbx_item.setBrush(brushC)
                bbx_item.setPen(QPen(QColor(0, 0, 255)))
            elif bbx_dict['label'].split('_')[0] == 'moderate':
                transparentC = QColor(255, 255, 0, 28)
                brushC = QBrush(transparentC)
                bbx_item.setBrush(brushC)
                bbx_item.setPen(QPen(QColor(255, 255, 0)))
            elif bbx_dict['label'].split('_')[0] == 'severe':
                transparentC = QColor(255, 0, 0, 28)
                brushC = QBrush(transparentC)
                bbx_item.setBrush(brushC)
                bbx_item.setPen(QPen(QColor(255, 0, 0)))
            bbx_item.setData(0, bbx_dict['label'])
            bbx_item.setAcceptHoverEvents(True)
            self.anno_scene.addItem(bbx_item)
            # self.view.annBBxes[bbx_dict['label']] = bbx_item
            uid = str(uuid.uuid4())
            bbx_item.setData(0, uid)
            self.view.annBBxes[uid] = {'label': bbx_dict['label'], 'item': bbx_item}

    @Slot()
    def save_anno(self):
        img_pth = self.init_img
        img_name = img_pth.split('/')[-1]
        patient_ID = img_name.split('_')[0]
        video_ID = img_name.split('-')[0]
        sv_pth = os.path.join(self.save_root, patient_ID, video_ID)
        sv_pth = sv_pth.replace('\\', '/')
        if not os.path.exists(sv_pth):
            os.makedirs(sv_pth)

        ann_txt = os.path.join(sv_pth, img_name.split('.')[0]+'.txt')
        
        all_bbxes = []

        if self.view.delBBxes:
            for i in self.view.delBBxes:
                crop_name = img_name.split('.')[0]+'_'+i+'.jpg'
                sv_img_pth = os.path.join(sv_pth, crop_name)
                sv_img_pth = sv_img_pth.replace('\\', '/')
                if os.path.exists(sv_img_pth):
                    os.remove(sv_img_pth)

        # for i, (k, bbx) in enumerate(self.view.annBBxes.items()):
        for i, (uid, info) in enumerate(self.view.annBBxes.items()):
            bbx_item = info['item']
            label = info['label']
            bbx = bbx_item.sceneBoundingRect()

            length = int(self.resize_info.split('*')[0])
            # topLx = bbx.rect().x()
            # topLy = bbx.rect().y()
            # width = bbx.rect().width()
            # height = bbx.rect().height()
            # bbx = bbx.sceneBoundingRect()    
            topLx = bbx.left()
            topLy = bbx.top()
            width = bbx.width()
            height = bbx.height()

            bottomRx = topLx+width
            bottomRy = topLy+height

            center_x = topLx+width/2
            center_y = topLy+height/2

            reLx = round(center_x-(length/2))
            reRy = round(center_y-(length/2))

            # k = k.split('_')[0]
            k = label.split('_')[0]
            re_label = k+'_'+str(i)                          # to delete the annotated image during using the software
            self.view.annBBxes[uid]['label'] = re_label      # relabel the stenosis annotaion to match the image_name
            crop_name = img_name.split('.')[0]+'_'+k+'_'+str(i)+'.jpg'

            sv_img_pth = os.path.join(sv_pth, crop_name)

            ori_img = cv2.imread(img_pth)
            crop_img = ori_img[reRy:reRy+length, reLx:reLx+length]       #opencv --> crop(y1:y2, x1:x2) 
            cv2.imwrite(sv_img_pth, crop_img)

            acs_cls = ''.join(filter(lambda x: not x.isdigit(), patient_ID))
            bbox_infos = {'TopLx':topLx, 'TopLy':topLy, 'BottomRx':bottomRx, 'BottomRy':bottomRy, 
                        'ACS_class':acs_cls, 'label':k+'_'+str(i)}
            bbox_infos = json.dumps(bbox_infos)
            all_bbxes.append(bbox_infos)

        with open(ann_txt, 'w', encoding='utf-8') as txt_file:
            for i in all_bbxes:
                txt_file.writelines(i+'\n')

    @Slot()
    def close_window(self):
        self.close()

class AnnotedView(QGraphicsView):
    # Using RubberBand as the Interaction with user, 2025/10/04 
    # author: krlab-ma, 256013s@gs.kochi-tech.ac.jp
    def __init__(self, scene, image_item, annoing_label):
        super().__init__(scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.image_item = image_item
        self.img_rect = image_item.boundingRect()                                      # setting coordinates inside image area, 2025.12.06
        self.start_pos = None
        self.labeling = False
        self.annBBxes = {}
        self.delBBxes = []
        # self.num_nnx = 0
        self.annoing_label = annoing_label

    def mousePressEvent(self, event):
        if self.annoing_label is True and event.button() == Qt.MouseButton.LeftButton:
            # if not self.img_rect.contains(current_pos):
            #     return 
            bbx_item = self.itemAt(event.pos())
            if isinstance(bbx_item, Editable2bbx):
                self.labeling = False
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
            else:
                self.start_pos = self.mapToScene(event.pos().x(), event.pos().y())
                self.labeling = True
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.annoing_label is True and event.button() == Qt.MouseButton.LeftButton:
            if self.labeling and self.start_pos is not None:
                end_pos = self.mapToScene(event.pos().x(), event.pos().y())
                rubber_bbx = QRectF(self.start_pos, end_pos).normalized()
                
                # This two lines to keep the bbxes drawing limited inside the image area. 2025.12.05
                # img_rect = self.image_item.boundingRect()
                img_rect = self.image_item.mapRectToScene(self.image_item.boundingRect())
                selected_bbx = rubber_bbx.intersected(img_rect)

                if selected_bbx.isValid() and selected_bbx.width()>5 and selected_bbx.height()>5:
                    bbx_item = Editable2bbx(selected_bbx, img_rect)
                    bbx_item.setAcceptHoverEvents(True)
                    # self.scene().addItem(bbx_item)
                    uid = str(uuid.uuid4())
                    bbx_item.setData(0, uid)
                    self.annBBxes[uid] = {'label': None, 'item': bbx_item}
                    self.scene().addItem(bbx_item)

            self.start_pos = None
            self.labeling = False
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        super().mouseReleaseEvent(event)

    # push RightButton of Mouse for giving the blockage level corresponding to annotation
    #                               or deleting the annotated bbx
    def contextMenuEvent(self, event):
        bbx_item = self.itemAt(event.pos())
        if isinstance(bbx_item, Editable2bbx):
            self.labeling = False
            menu = QMenu(self)
            mild_action = menu.addAction("Type: mild (blockage<=50%)")
            moderate_action = menu.addAction("Type: moderate (50%<blockage<=70%)")
            severe_action = menu.addAction("Type: severe (70%<blockage)")
            delete_action = menu.addAction("このアノテーションを削除します")
            action = menu.exec(event.globalPos())
            if action == delete_action:
                sakujyo = QMessageBox.question(self, "確認してください", "削除/キャンセル",
                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
                if sakujyo == QMessageBox.StandardButton.Ok:
                    if len(self.annBBxes) != 0:
                        if bbx_item.data(0):
                            # del self.annBBxes[bbx_item.data(0)]
                            # self.delBBxes.append(bbx_item.data(0))
                            uid = bbx_item.data(0)
                            name = self.annBBxes[uid]['label']
                            self.delBBxes.append(name)
                            self.annBBxes.pop(uid, None)
                            self.scene().removeItem(bbx_item)
                    self.scene().removeItem(bbx_item)
            elif action == mild_action:
                transparentC = QColor(0, 0, 255, 28)
                brushC = QBrush(transparentC)
                bbx_item.setBrush(brushC)
                bbx_item.setPen(QPen(QColor(0, 0, 255)))
                grad_text = action.text().split(' ')[1]
                # self.annBBxes[grad_text] = bbx_item
                uid = bbx_item.data(0)
                self.annBBxes[uid]['label'] = 'mild'
            elif action == moderate_action:
                transparentC = QColor(255, 255, 0, 28)
                brushC = QBrush(transparentC)
                bbx_item.setBrush(brushC)
                bbx_item.setPen(QPen(QColor(255, 255, 0)))
                grad_text = action.text().split(' ')[1]
                # self.annBBxes[grad_text] = bbx_item
                uid = bbx_item.data(0)
                self.annBBxes[uid]['label'] = 'moderate'
            elif action == severe_action:
                transparentC = QColor(255, 0, 0, 28)
                brushC = QBrush(transparentC)
                bbx_item.setBrush(brushC)
                bbx_item.setPen(QPen(QColor(255, 0, 0)))
                grad_text = action.text().split(' ')[1]
                # self.annBBxes[grad_text] = bbx_item
                uid = bbx_item.data(0)
                self.annBBxes[uid]['label'] = 'severe'

        super().contextMenuEvent(event)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.image_item, Qt.KeepAspectRatio)

class Editable2bbx(QObject, QGraphicsRectItem):
    cursors_size = 6
    cursors = {'tl':Qt.CursorShape.SizeFDiagCursor, 'tr':Qt.CursorShape.SizeBDiagCursor,
                'tm':Qt.CursorShape.SizeVerCursor, 'bm':Qt.CursorShape.SizeVerCursor,
                'bl':Qt.CursorShape.SizeBDiagCursor, 'br':Qt.CursorShape.SizeFDiagCursor,
                'lm':Qt.CursorShape.SizeHorCursor, 'rm':Qt.CursorShape.SizeHorCursor, 
                'cp':Qt.CursorShape.CrossCursor}
    anno_moved = Signal(QRectF)

    def __init__(self, rect=QRectF, img_rect=QRectF):
        QObject.__init__(self)
        QGraphicsRectItem.__init__(self, rect)
        self.setPen(QPen(QColor(255, 0, 0), 2))
        transparentC = QColor(0, 0, 0, 28)
        brushC = QBrush(transparentC)
        self.setBrush(brushC)
        self.setFlags(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable 
                    | QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
                    | QGraphicsRectItem.ItemSendsScenePositionChanges)
        self.edit_cursors = {}
        self.crusors_selected = False
        self.bbx_selected = None

        self.img_rect = img_rect
        self.update_cursors()

    def boundingRect(self):
        # raduis = Editable2bbx.cursors_size
        # return self.rect().adjusted(-raduis, -raduis, raduis, raduis)
        return self.rect()
    
    def update_cursors(self):
        bbx_item = QGraphicsRectItem(self.rect())
        bbx_item.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine))
        bbx = self.rect()
        raduis = Editable2bbx.cursors_size
        self.edit_cursors = {
                            "tl": QRectF(bbx.left() - raduis/2, bbx.top() - raduis/2, raduis, raduis),
                            "tr": QRectF(bbx.right() - raduis/2, bbx.top() - raduis/2, raduis, raduis),
                            "bl": QRectF(bbx.left() - raduis/2, bbx.bottom() - raduis/2, raduis, raduis),
                            "br": QRectF(bbx.right() - raduis/2, bbx.bottom() - raduis/2, raduis, raduis),
                            "tm": QRectF(bbx.center().x() - raduis/2, bbx.top() - raduis/2, raduis, raduis),
                            "bm": QRectF(bbx.center().x() - raduis/2, bbx.bottom() - raduis/2, raduis, raduis),
                            "lm": QRectF(bbx.left() - raduis/2, bbx.center().y() - raduis/2, raduis, raduis),
                            "rm": QRectF(bbx.right() - raduis/2, bbx.center().y() - raduis/2, raduis, raduis),
                            "cp": QRectF(bbx.center().x()- raduis/2, bbx.center().y()- raduis/2, raduis, raduis)
                            }

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 255, 0)))
            painter.drawPoint(255,255)
            # for cursor in self.edit_cursors.values():
            #     painter.drawRect(cursor)
            for key, cursor in self.edit_cursors.items():
                if key == 'cp':
                     painter.setBrush(QBrush(QColor(0, 0, 0, 0)))  
                painter.drawRect(cursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            for vertex, sign in self.edit_cursors.items():
                if sign.contains(event.pos()):
                    self.bbx_selected = vertex
                    break
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.bbx_selected is not None:
            edit_pos = event.pos()
            bbx = self.rect()
            if self.bbx_selected == 'tl':
                bbx.setTopLeft(edit_pos)
            elif self.bbx_selected == 'tr':
                bbx.setTopRight(edit_pos)
            elif self.bbx_selected == 'bl':
                bbx.setBottomLeft(edit_pos)
            elif self.bbx_selected == 'br':
                bbx.setBottomRight(edit_pos)
            elif self.bbx_selected == 'lm':
                bbx.setLeft(edit_pos.x())
            elif self.bbx_selected == 'rm':
                bbx.setRight(edit_pos.x())
            elif self.bbx_selected == 'tm':
                bbx.setTop(edit_pos.y())
            elif self.bbx_selected == 'bm':
                bbx.setBottom(edit_pos.y())
            self.setRect(bbx.normalized())        # !!Dont forget this line to update the bbx after editing!!
            self.update_cursors()
            self.update()
            # self.anno_moved.emit(self.rect())
            self.anno_moved.emit(self.sceneBoundingRect())
        else:
            super().mouseMoveEvent(event)
            # self.anno_moved.emit(self.rect())
            self.anno_moved.emit(self.sceneBoundingRect())

    def mouseReleaseEvent(self, event):
        self.bbx_selected = None
        # self.anno_moved.emit(self.rect())
        self.anno_moved.emit(self.sceneBoundingRect())
        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        if self.isSelected():
            for vertex, sign in self.edit_cursors.items():
                if sign.contains(event.pos()):
                    self.setCursor(self.cursors[vertex])
                    return
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().hoverMoveEvent(event)

if __name__ == "__main__":
    save_root = 'D:/test_dataset/Save_Anno'
    resize_info = 64
    app = QApplication(sys.argv)
    window = label_main(resize_info, save_root)
    window.show()
    sys.exit(app.exec())